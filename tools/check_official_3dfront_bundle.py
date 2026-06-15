#!/usr/bin/env python3
"""Check whether a candidate 3D-FRONT / 3D-FUTURE directory is official-like.

Read-only inspection only: no conversion, training, model loading, or downloads.
"""
from __future__ import annotations

import argparse
import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_FRONT_KEYS = {"uid", "scene", "furniture", "mesh", "material", "north_vector"}
PROCESSED_LIKE_FIELDS = {"room_mask", "semantic_map", "label_map", "boxes", "npy_path", "prompt", "edit_instruction"}


def safe_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore")), None
    except Exception as exc:
        return None, repr(exc)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def iter_files_limited(root: Path, suffixes: set[str] | None = None, limit: int = 300) -> list[Path]:
    found: list[Path] = []
    if not root.exists():
        return found
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        found.append(path)
        if len(found) >= limit:
            break
    return found


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
    jids: list[str] = []
    def scan(x: Any, depth: int = 0) -> None:
        if depth > 5 or len(jids) >= limit:
            return
        if isinstance(x, dict):
            jid = x.get("jid")
            if isinstance(jid, str) and jid.strip():
                jids.append(jid)
            for value in x.values():
                scan(value, depth + 1)
        elif isinstance(x, list):
            for value in x[:200]:
                scan(value, depth + 1)
    scan(obj)
    return jids


def inspect_bundle(dataset_bundle: Path, max_scenes: int) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    front_scene = dataset_bundle / "3D-FRONT"
    front_texture = dataset_bundle / "3D-FRONT-texture"
    future_model = dataset_bundle / "3D-FUTURE-model"
    children = sorted([p.name for p in dataset_bundle.iterdir()]) if dataset_bundle.exists() else []
    front_jsons = sorted(front_scene.glob("*.json")) if front_scene.exists() else []
    future_model_dirs = [p for p in future_model.iterdir() if p.is_dir()] if future_model.exists() else []
    raw_model_obj_count = 0
    for model_dir in future_model_dirs:
        if (model_dir / "raw_model.obj").exists():
            raw_model_obj_count += 1
    official_like = bool(front_jsons and front_texture.exists() and (future_model / "model_info.json").exists() and raw_model_obj_count > 0)
    bundle = {
        "status": "official-like" if official_like else ("incomplete" if dataset_bundle.exists() else "unknown"),
        "exists": dataset_bundle.exists(),
        "children": children,
        "front_scene_exists": front_scene.exists(),
        "front_texture_exists": front_texture.exists(),
        "future_model_exists": future_model.exists(),
        "front_json_count": len(front_jsons),
        "texture_exists": front_texture.exists(),
        "model_info_exists": (future_model / "model_info.json").exists(),
        "future_model_dir_count": len(future_model_dirs),
        "raw_model_obj_count_estimate": raw_model_obj_count,
    }

    top_counter: Counter[str] = Counter()
    processed_fields: set[str] = set()
    scene_like_flags = []
    sample_records = []
    sample_jids: list[str] = []
    for path in front_jsons[:max_scenes]:
        data, error = safe_json(path)
        item: dict[str, Any] = {"path": str(path), "relative": str(path.relative_to(front_scene))}
        if error:
            item["error"] = error
            sample_records.append(item)
            continue
        if isinstance(data, dict):
            keys = set(data.keys())
            top_counter.update(keys)
            all_keys = nested_keys(data)
            processed_fields.update(all_keys & PROCESSED_LIKE_FIELDS)
            furniture = data.get("furniture")
            scene = data.get("scene")
            item["top_level_keys"] = sorted(keys)
            item["required_raw_key_hits"] = sorted(keys & REQUIRED_FRONT_KEYS)
            item["furniture_is_list"] = isinstance(furniture, list)
            if isinstance(furniture, list) and furniture:
                item["furniture_entry_keys"] = sorted({str(k) for entry in furniture[:20] if isinstance(entry, dict) for k in entry.keys()})[:80]
                item["furniture_entry_has_uid_jid"] = any(isinstance(entry, dict) and {"uid", "jid"}.issubset(entry) for entry in furniture[:20])
            item["scene_summary"] = {"type": type(scene).__name__}
            if isinstance(scene, dict):
                item["scene_keys"] = list(scene.keys())[:80]
            item["room_children_node_candidates"] = sorted([k for k in all_keys if any(t in k.lower() for t in ["room", "children", "node"])])[:80]
            item["processed_like_fields_found"] = sorted(all_keys & PROCESSED_LIKE_FIELDS)
            scene_like_flags.append(REQUIRED_FRONT_KEYS.issubset(keys) and isinstance(furniture, list) and isinstance(scene, dict))
            sample_jids.extend(collect_jids(data))
        else:
            item["top_type"] = type(data).__name__
            scene_like_flags.append(False)
        sample_records.append(item)
    raw_likeness = {
        "sample_count": len(sample_records),
        "common_top_level_keys": [key for key, count in top_counter.most_common() if count >= max(1, len(sample_records) // 2)],
        "all_top_level_keys": sorted(top_counter),
        "raw_scene_like": bool(scene_like_flags) and sum(scene_like_flags) >= max(1, len(scene_like_flags) // 2),
        "processed_like_fields_found": sorted(processed_fields),
        "sample_scenes": sample_records,
        "sample_front_jids": sorted(set(sample_jids))[:200],
    }
    return bundle, raw_likeness, sorted(set(sample_jids))


def inspect_future_models(future_model: Path, front_jids: list[str], max_models: int) -> tuple[dict[str, Any], dict[str, Any]]:
    model_info = future_model / "model_info.json"
    data, error = safe_json(model_info) if model_info.exists() else (None, "model_info.json missing")
    model_entries = data if isinstance(data, list) else []
    keys = sorted({str(k) for item in model_entries[:max_models] if isinstance(item, dict) for k in item.keys()})
    index: dict[str, dict[str, Any]] = {}
    for item in model_entries:
        if not isinstance(item, dict):
            continue
        model_id = item.get("model_id") or item.get("jid") or item.get("uid") or item.get("id")
        if isinstance(model_id, str):
            index[model_id] = item
    nonempty_jids = [jid for jid in front_jids if jid]
    matched = []
    unmatched = []
    for jid in nonempty_jids[:200]:
        item = index.get(jid)
        if item:
            matched.append({"jid": jid, "category": item.get("category"), "super_category": item.get("super-category")})
        else:
            unmatched.append(jid)
    denominator = len(matched) + len(unmatched)
    match = {
        "front_jid_count": len(nonempty_jids),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "match_rate": round(len(matched) / denominator, 4) if denominator else 0.0,
        "matched_samples": matched[:20],
        "unmatched_samples": unmatched[:20],
    }

    raw_found = norm_found = texture_like = 0
    missing_dirs = []
    for item in model_entries[:max_models]:
        if not isinstance(item, dict):
            continue
        model_id = item.get("model_id")
        if not isinstance(model_id, str):
            continue
        model_dir = future_model / model_id
        if not model_dir.exists():
            missing_dirs.append(model_id)
            continue
        if (model_dir / "raw_model.obj").exists():
            raw_found += 1
        if (model_dir / "normalized_model.obj").exists():
            norm_found += 1
        try:
            if any(p.is_file() and (p.suffix.lower() in {".png", ".jpg", ".jpeg"} or "texture" in p.name.lower() or "material" in p.name.lower()) for p in model_dir.rglob("*")):
                texture_like += 1
        except OSError:
            pass
    files = {
        "sample_count": min(max_models, len(model_entries)),
        "raw_model_obj_found": raw_found,
        "normalized_model_obj_found": norm_found,
        "texture_like_files_found": texture_like,
        "missing_model_dirs": missing_dirs[:50],
    }
    future = {
        "model_info_exists": model_info.exists(),
        "model_info_error": error,
        "model_count": len(model_entries),
        "entry_key_candidates": keys,
        "id_field_candidates": [k for k in keys if any(t in k.lower() for t in ["id", "uid", "jid", "model"])],
        "category_field_candidates": [k for k in keys if any(t in k.lower() for t in ["category", "class", "name"])],
        "style_theme_material_fields": [k for k in keys if any(t in k.lower() for t in ["style", "theme", "material"])],
        "sample_models": [item for item in model_entries[:max_models] if isinstance(item, dict)][:10],
        "jid_model_info_match": match,
    }
    return future, files


def inspect_editroom(editroom_root: Path, dataset_bundle: Path) -> dict[str, Any]:
    return {
        "editroom_root_exists": editroom_root.exists(),
        "datasets_exists": (editroom_root / "datasets").exists(),
        "configs_exists": (editroom_root / "configs").exists(),
        "train_edit_exists": (editroom_root / "src" / "train_edit.py").exists(),
        "data_location_context": "inside_editroom_datasets" if str(dataset_bundle).startswith(str(editroom_root / "datasets")) else "outside_editroom_datasets",
        "interpretation": "The bundle is located under EditRoom datasets. This suggests a copied or organized dataset for EditRoom use, not proof that scene/model files are modified.",
        "impact_on_loreflection": "Can be used as a raw source if official-like consistency checks pass; keep provenance note in reports.",
    }


def png_info(path: Path) -> dict[str, Any]:
    item: dict[str, Any] = {"path": str(path)}
    try:
        head = path.read_bytes()[:32]
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height = struct.unpack(">II", head[16:24])
            item.update({"width": width, "height": height, "png": True})
    except Exception as exc:
        item["error"] = repr(exc)
    return item


def inspect_semlayoutdiff(root: Path) -> dict[str, Any]:
    raw_bundle_like = (root / "3D-FRONT").exists() and (root / "3D-FUTURE-model" / "model_info.json").exists()
    jsons: list[Path] = []
    pngs: list[Path] = []
    npys: list[Path] = []
    pkls: list[Path] = []
    for path in root.rglob("*") if root.exists() else []:
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        name = path.name.lower()
        if suffix == ".png" and ("updated_bottom_label_map" in name or "semantic" in name or "label" in name):
            pngs.append(path)
        elif suffix == ".json" and ("meta" in name or "anno" in name or len(jsons) < 30):
            jsons.append(path)
        elif suffix in {".npy", ".npz"}:
            npys.append(path)
        elif suffix == ".pkl":
            pkls.append(path)
        if len(jsons) >= 50 and len(pngs) >= 50 and len(npys) >= 20 and len(pkls) >= 20:
            break
    role = "raw_bundle_candidate" if raw_bundle_like else ("processed_or_rendered" if pngs or npys or pkls or jsons else "unknown")
    return {
        "root_exists": root.exists(),
        "semlayoutdiff_data_role": role,
        "raw_bundle_like": raw_bundle_like,
        "semantic_png_candidates": [png_info(p) for p in pngs[:20]],
        "json_candidates": [str(p) for p in jsons[:20]],
        "npy_candidates": [str(p) for p in npys[:20]],
        "pkl_candidates": [str(p) for p in pkls[:20]],
        "should_use_as_raw_source": "yes" if raw_bundle_like else "no",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-bundle", type=Path, required=True)
    parser.add_argument("--semlayoutdiff-root", type=Path, required=True)
    parser.add_argument("--editroom-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-scenes", type=int, default=20)
    parser.add_argument("--max-models", type=int, default=50)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    front_scene = args.dataset_bundle / "3D-FRONT"
    front_texture = args.dataset_bundle / "3D-FRONT-texture"
    future_model = args.dataset_bundle / "3D-FUTURE-model"
    bundle, raw_likeness, front_jids = inspect_bundle(args.dataset_bundle, args.max_scenes)
    future, future_files = inspect_future_models(future_model, front_jids, args.max_models)
    editroom = inspect_editroom(args.editroom_root, args.dataset_bundle)
    semlayoutdiff = inspect_semlayoutdiff(args.semlayoutdiff_root)

    high_conf = bundle["status"] == "official-like" and raw_likeness.get("raw_scene_like") and future["jid_model_info_match"]["match_rate"] >= 0.2 and future_files["raw_model_obj_found"] > 0
    notes = []
    if editroom["data_location_context"] == "inside_editroom_datasets":
        notes.append("Dataset bundle is inside EditRoom datasets; treat as official-like copied bundle unless file-level differences are later found.")
    if semlayoutdiff["semlayoutdiff_data_role"] == "processed_or_rendered":
        notes.append("Use SemLayoutDiff outputs as processed/rendered semantic sources, not canonical raw roots.")
    report = {
        "report_version": "official_3dfront_bundle_check_v1",
        "schema_version": "official-3dfront-bundle-check-v1",
        "paths": {
            "dataset_bundle": str(args.dataset_bundle),
            "front_scene": str(front_scene),
            "front_texture": str(front_texture),
            "future_model": str(future_model),
            "semlayoutdiff_root": str(args.semlayoutdiff_root),
            "editroom_root": str(args.editroom_root),
        },
        "bundle_structure": bundle,
        "front_json_raw_likeness": raw_likeness,
        "threed_future_model_info": future,
        "jid_model_info_match": future["jid_model_info_match"],
        "future_model_files": future_files,
        "editroom_context": editroom,
        "semlayoutdiff_context": semlayoutdiff,
        "recommendation": {
            "canonical_raw_bundle_root": str(args.dataset_bundle),
            "canonical_front_scene_root": str(front_scene),
            "canonical_future_model_root": str(future_model),
            "canonical_texture_root": str(front_texture),
            "use_for_loreflection": "yes" if high_conf else "partial",
            "confidence": "high" if high_conf else "medium",
            "notes": notes,
        },
    }
    write_json(args.output, report)
    if args.verbose:
        print(json.dumps({
            "bundle_status": bundle["status"],
            "front_json_count": bundle["front_json_count"],
            "model_count": future["model_count"],
            "jid_match_rate": future["jid_model_info_match"]["match_rate"],
            "confidence": report["recommendation"]["confidence"],
            "output": str(args.output),
        }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
