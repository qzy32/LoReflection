#!/usr/bin/env python3
"""Analyze provenance and usage gaps for an EditRoom-provided 3D-FRONT bundle.

Read-only inspection only. This script does not download data, train models,
run conversion, or execute third-party pipelines.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

OFFICIAL_TOP_KEYS = {"uid", "scene", "furniture", "mesh", "material"}
PROCESSED_HINTS = {"room_mask", "semantic_map", "label_map", "boxes", "npy_path", "prompt", "edit_instruction"}


def safe_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore")), None
    except Exception as exc:
        return None, repr(exc)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def nested_keys(obj: Any, depth: int = 0, max_depth: int = 4) -> set[str]:
    keys: set[str] = set()
    if depth > max_depth:
        return keys
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.add(str(key))
            keys.update(nested_keys(value, depth + 1, max_depth))
    elif isinstance(obj, list):
        for value in obj[:20]:
            keys.update(nested_keys(value, depth + 1, max_depth))
    return keys


def collect_jids(obj: Any, limit: int = 1000) -> list[str]:
    out: list[str] = []
    def scan(x: Any, depth: int = 0) -> None:
        if depth > 6 or len(out) >= limit:
            return
        if isinstance(x, dict):
            jid = x.get("jid")
            if isinstance(jid, str) and jid.strip():
                out.append(jid)
            for value in x.values():
                scan(value, depth + 1)
        elif isinstance(x, list):
            for value in x[:200]:
                scan(value, depth + 1)
    scan(obj)
    return out


def count_dirs(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.iterdir() if p.is_dir())


def estimate_raw_model_sample(future_root: Path, model_ids: list[str], max_models: int) -> dict[str, Any]:
    raw = norm = texture = 0
    missing_dirs = []
    for model_id in model_ids[:max_models]:
        d = future_root / model_id
        if not d.exists():
            missing_dirs.append(model_id)
            continue
        if (d / "raw_model.obj").exists():
            raw += 1
        if (d / "normalized_model.obj").exists():
            norm += 1
        try:
            if any(p.is_file() and (p.suffix.lower() in {".png", ".jpg", ".jpeg"} or "texture" in p.name.lower() or "material" in p.name.lower()) for p in d.rglob("*")):
                texture += 1
        except OSError:
            pass
    return {
        "sample_count": min(max_models, len(model_ids)),
        "raw_model_obj_found": raw,
        "normalized_model_obj_found": norm,
        "texture_like_files_found": texture,
        "missing_model_dirs": missing_dirs[:50],
    }


def inspect_current_bundle(dataset_bundle: Path, front_root: Path, future_root: Path, texture_root: Path, max_scenes: int, max_models: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    scene_jsons = sorted(front_root.glob("*.json")) if front_root.exists() else []
    model_info = future_root / "model_info.json"
    model_data, model_error = safe_json(model_info) if model_info.exists() else (None, "missing")
    model_entries = model_data if isinstance(model_data, list) else []
    model_ids = [x.get("model_id") for x in model_entries if isinstance(x, dict) and isinstance(x.get("model_id"), str)]
    future_dirs = count_dirs(future_root)
    extra_files = [name for name in ["threed_front.pkl", "3D-FRONT-readme.md"] if (dataset_bundle / name).exists()]

    top_counter: Counter[str] = Counter()
    processed_fields = set()
    raw_like_flags = []
    front_jids: list[str] = []
    sample_scenes = []
    for path in scene_jsons[:max_scenes]:
        data, error = safe_json(path)
        item: dict[str, Any] = {"path": str(path), "relative": str(path.relative_to(front_root))}
        if error:
            item["error"] = error
            sample_scenes.append(item)
            continue
        if isinstance(data, dict):
            keys = set(data.keys())
            all_keys = nested_keys(data)
            top_counter.update(keys)
            processed_fields.update(all_keys & PROCESSED_HINTS)
            furniture = data.get("furniture")
            item["top_level_keys"] = sorted(keys)
            item["official_key_hits"] = sorted(keys & OFFICIAL_TOP_KEYS)
            item["furniture_is_list"] = isinstance(furniture, list)
            item["scene_is_dict"] = isinstance(data.get("scene"), dict)
            if isinstance(furniture, list) and furniture:
                item["furniture_entry_keys"] = sorted({str(k) for f in furniture[:20] if isinstance(f, dict) for k in f.keys()})
            raw_like_flags.append(OFFICIAL_TOP_KEYS.issubset(keys) and isinstance(furniture, list) and isinstance(data.get("scene"), dict))
            front_jids.extend(collect_jids(data))
        else:
            item["top_type"] = type(data).__name__
            raw_like_flags.append(False)
        sample_scenes.append(item)

    model_index = {x.get("model_id"): x for x in model_entries if isinstance(x, dict) and isinstance(x.get("model_id"), str)}
    nonempty_jids = [j for j in sorted(set(front_jids)) if j]
    matched = []
    unmatched = []
    for jid in nonempty_jids[:300]:
        meta = model_index.get(jid)
        if meta:
            matched.append({"jid": jid, "category": meta.get("category"), "super_category": meta.get("super-category")})
        else:
            unmatched.append(jid)
    denom = len(matched) + len(unmatched)

    current = {
        "dataset_bundle_exists": dataset_bundle.exists(),
        "scene_json_count": len(scene_jsons),
        "model_info_exists": model_info.exists(),
        "model_info_error": model_error,
        "model_info_count": len(model_entries),
        "model_directory_count": future_dirs,
        "texture_directory_exists": texture_root.exists(),
        "extra_files": extra_files,
        "inside_editroom_datasets": "/EditRoom/datasets/" in str(dataset_bundle),
        "raw_model_sample": estimate_raw_model_sample(future_root, model_ids, max_models),
    }
    official_like = {
        "has_front_json": bool(scene_jsons),
        "has_raw_scene_top_keys": bool(raw_like_flags) and sum(raw_like_flags) >= max(1, len(raw_like_flags) // 2),
        "common_top_level_keys": [k for k, _ in top_counter.most_common()],
        "processed_like_fields_found": sorted(processed_fields),
        "has_future_model_info": model_info.exists(),
        "model_info_has_model_id": any("model_id" in x for x in model_entries[:max_models] if isinstance(x, dict)),
        "model_info_has_category": any("category" in x for x in model_entries[:max_models] if isinstance(x, dict)),
        "has_raw_model_obj": current["raw_model_sample"]["raw_model_obj_found"] > 0,
        "has_texture_root": texture_root.exists(),
        "sample_scenes": sample_scenes,
        "front_json_raw_likeness": {
            "sample_count": len(sample_scenes),
            "common_top_level_keys": [k for k, count in top_counter.most_common() if count >= max(1, len(sample_scenes) // 2)],
            "raw_scene_like": bool(raw_like_flags) and sum(raw_like_flags) >= max(1, len(raw_like_flags) // 2),
            "processed_like_fields_found": sorted(processed_fields),
        },
        "jid_model_info_match": {
            "front_jid_count": len(nonempty_jids),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "match_rate": round(len(matched) / denom, 4) if denom else 0.0,
            "matched_samples": matched[:20],
            "unmatched_samples": unmatched[:20],
        },
    }
    return current, official_like, {"front_jids": nonempty_jids, "model_ids": model_ids}


def inspect_derivative_evidence(dataset_bundle: Path, editroom_root: Path) -> dict[str, Any]:
    readme_candidates = [editroom_root / "README.md", editroom_root / "readme.md", dataset_bundle / "3D-FRONT-readme.md"]
    keyword_hits = []
    for path in readme_candidates:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")[:200000]
        for keyword in ["preprocessed", "preprocessed datasets", "download_dataset.py", "InstructScene", "perturb", "editing", "prompt"]:
            if keyword.lower() in text.lower():
                keyword_hits.append({"file": str(path), "keyword": keyword})
    files = []
    for pattern in ["download_dataset.py", "*InstructScene*", "*perturb*", "*prompt*", "*edit*manifest*", "*.pkl"]:
        try:
            files.extend(str(p) for p in editroom_root.rglob(pattern) if p.is_file())
        except OSError:
            pass
    processed_like = [str(dataset_bundle / "threed_front.pkl")] if (dataset_bundle / "threed_front.pkl").exists() else []
    return {
        "threed_front_pkl_exists": (dataset_bundle / "threed_front.pkl").exists(),
        "readme_keyword_hits": keyword_hits[:80],
        "editroom_related_file_candidates": sorted(set(files))[:120],
        "processed_or_derivative_file_evidence": processed_like,
    }


def risk_and_policy() -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    risk = {
        "provenance_risk": "medium",
        "field_modification_risk": "low",
        "split_mismatch_risk": "medium",
        "license_reproducibility_risk": "medium",
        "baseline_fairness_risk": "medium",
    }
    usage_policy = {
        "allowed_for": [
            "converter prototype",
            "field mapping",
            "val50 prototype",
            "debugging LoReflection pipeline",
        ],
        "not_recommended_for": [
            "final main experiment unless provenance is disclosed",
            "claiming official raw dataset",
            "strict baseline comparison without split alignment",
        ],
        "required_before_main_experiment": [
            "obtain official raw bundle or verify checksums/splits against official source",
            "document provenance",
            "run converter regression on official or verified source",
            "freeze train/val/test split",
        ],
    }
    migration_plan = [
        "place official bundle under /wuqingyaoa800/qiuziyan/datasets/official_3dfront_bundle",
        "rerun provenance check",
        "rerun field mapping report",
        "rerun 5-scene converter prototype",
        "compare category histogram / jid match / room type distribution",
        "rerun val50",
        "only then build training 1k",
    ]
    return risk, usage_policy, migration_plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-bundle", type=Path, required=True)
    parser.add_argument("--front-root", type=Path, required=True)
    parser.add_argument("--future-root", type=Path, required=True)
    parser.add_argument("--texture-root", type=Path, required=True)
    parser.add_argument("--editroom-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-scenes", type=int, default=20)
    parser.add_argument("--max-models", type=int, default=50)
    args = parser.parse_args()

    current, official_like, ids = inspect_current_bundle(args.dataset_bundle, args.front_root, args.future_root, args.texture_root, args.max_scenes, args.max_models)
    derivative = inspect_derivative_evidence(args.dataset_bundle, args.editroom_root)
    risk, usage_policy, migration_plan = risk_and_policy()
    official_like_bool = all([
        official_like["has_front_json"],
        official_like["has_raw_scene_top_keys"],
        official_like["has_future_model_info"],
        official_like["model_info_has_model_id"],
        official_like["model_info_has_category"],
        official_like["has_raw_model_obj"],
        official_like["has_texture_root"],
    ])
    preprocessed_or_derivative = bool(current["inside_editroom_datasets"] or derivative["threed_front_pkl_exists"] or derivative["readme_keyword_hits"])
    report = {
        "report_version": "dataset_source_gap_analysis_v1",
        "schema_version": "dataset-source-gap-analysis-v1",
        "paths": {
            "dataset_bundle": str(args.dataset_bundle),
            "front_root": str(args.front_root),
            "future_root": str(args.future_root),
            "texture_root": str(args.texture_root),
            "editroom_root": str(args.editroom_root),
        },
        "current_bundle_profile": current,
        "classification": {
            "official_like": official_like_bool,
            "editroom_provided": current["inside_editroom_datasets"],
            "preprocessed_or_derivative": preprocessed_or_derivative,
            "safe_wording": "EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle",
        },
        "official_like_evidence": official_like,
        "derivative_preprocessed_evidence": derivative,
        "risk": risk,
        "usage_policy": usage_policy,
        "migration_plan_if_official_raw_bundle_obtained": migration_plan,
        "recommendation": {
            "can_continue_val50_prototype": True,
            "can_use_for_final_aaai_main_experiment": "only with provenance disclosure or after checksum/split verification",
            "must_resolve_before_final_experiments": usage_policy["required_before_main_experiment"],
        },
    }
    write_json(args.output, report)
    print(json.dumps({
        "official_like": official_like_bool,
        "editroom_provided": current["inside_editroom_datasets"],
        "preprocessed_or_derivative": preprocessed_or_derivative,
        "scene_json_count": current["scene_json_count"],
        "model_info_count": current["model_info_count"],
        "jid_match_rate": official_like["jid_model_info_match"]["match_rate"],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
