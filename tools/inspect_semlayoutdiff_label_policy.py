#!/usr/bin/env python
"""Inspect SemLayoutDiff label and architecture-condition policy.

This read-only tool summarizes SemLayoutDiff metadata/config/code evidence for
architecture condition labels, furniture semantic labels, non-core object roles,
and processed output semantics. It does not execute SemLayoutDiff conversion,
load models, train, or modify third-party files.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "preprocess/metadata/room_type_furniture_priors_34class.json",
    "preprocess/metadata/semantic_color_index_bedroom.csv",
    "preprocess/metadata/semantic_color_index_livingdiningroom.csv",
    "preprocess/metadata/unified_idx_to_generic_label_w_arch.json",
    "preprocess/metadata/color_palette.json",
    "configs/data_processing.yaml",
    "preprocess/scripts/data_processor.py",
    "preprocess/scripts/json_threed_future_dataset.py",
]

ARCH_TERMS = ("room boundary", "boundary", "wall", "door", "window", "opening", "floor", "background")
NON_CORE_TERMS = ("door", "window", "curtain", "lamp", "ceiling lamp", "pendant lamp", "opening", "wall")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def file_status(root: Path) -> dict[str, str]:
    status = {}
    for item in REQUIRED_FILES:
        status[item] = "exists" if (root / item).exists() else "missing"
    apm_dir = root / "configs" / "apm"
    if apm_dir.exists():
        for path in sorted(apm_dir.glob("*.yaml"))[:40]:
            status[rel(path, root)] = "exists"
    return status


def parse_csv_labels(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        for row in csv.DictReader(f):
            rows.append({k: v for k, v in row.items()})
    return rows


def flatten_label_mapping(payload: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, dict):
                label = value.get("label") or value.get("name") or value.get("generic_label") or value.get("category") or value.get("en")
                out.append({"index": key, "label": label if label is not None else value, "raw": value})
            else:
                out.append({"index": key, "label": value, "raw": value})
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            if isinstance(value, dict):
                label = value.get("label") or value.get("name") or value.get("generic_label") or value.get("category") or value.get("en")
                out.append({"index": idx, "label": label if label is not None else value, "raw": value})
            else:
                out.append({"index": idx, "label": value, "raw": value})
    return out


def collect_metadata_labels(root: Path) -> dict[str, list[dict[str, Any]]]:
    sources: dict[str, list[dict[str, Any]]] = {}
    for rel_path in [
        "preprocess/metadata/semantic_color_index_bedroom.csv",
        "preprocess/metadata/semantic_color_index_livingdiningroom.csv",
    ]:
        path = root / rel_path
        rows = parse_csv_labels(path)
        if rows:
            sources[rel_path] = [
                {
                    "index": row.get("index") or row.get("id"),
                    "label": row.get("label") or row.get("name"),
                    "color": row.get("color"),
                    "raw": row,
                }
                for row in rows
            ]
    for rel_path in [
        "preprocess/metadata/unified_idx_to_generic_label_w_arch.json",
        "preprocess/metadata/color_palette.json",
        "preprocess/metadata/room_type_furniture_priors_34class.json",
    ]:
        path = root / rel_path
        if path.exists():
            try:
                sources[rel_path] = flatten_label_mapping(load_json(path))
            except Exception as exc:  # noqa: BLE001
                sources[rel_path] = [{"error": repr(exc)}]
    return sources


def grep_evidence(path: Path, terms: tuple[str, ...], max_hits: int = 16) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size > 1_500_000:
        return []
    hits = []
    lowered_terms = [(term, term.lower()) for term in terms]
    for lineno, line in enumerate(read_text(path).splitlines(), 1):
        lower = line.lower()
        found = [term for term, lowered in lowered_terms if lowered in lower]
        if not found:
            continue
        text = re.sub(r"\s+", " ", line.strip())
        hits.append({"file": path.as_posix(), "line": lineno, "terms": found, "text": text[:220]})
        if len(hits) >= max_hits:
            break
    return hits


def source_rel_evidence(root: Path, rel_paths: list[str], terms: tuple[str, ...]) -> list[dict[str, Any]]:
    evidence = []
    for rel_path in rel_paths:
        path = root / rel_path
        for item in grep_evidence(path, terms):
            item["file"] = rel(Path(item["file"]), root)
            evidence.append(item)
    apm_dir = root / "configs" / "apm"
    if apm_dir.exists():
        for path in sorted(apm_dir.glob("*.yaml"))[:20]:
            for item in grep_evidence(path, terms, max_hits=4):
                item["file"] = rel(Path(item["file"]), root)
                evidence.append(item)
    return evidence[:80]


def label_contains(label: Any, term: str) -> bool:
    return term.lower() in str(label or "").lower()


def find_label_terms(label_sources: dict[str, list[dict[str, Any]]], terms: tuple[str, ...]) -> dict[str, list[dict[str, Any]]]:
    result = {term: [] for term in terms}
    for source, rows in label_sources.items():
        for row in rows:
            label_text = json.dumps(row, ensure_ascii=False).lower()
            for term in terms:
                if term.lower() in label_text:
                    result[term].append({"source": source, "entry": row})
    return result


def infer_architecture_policy(label_sources: dict[str, list[dict[str, Any]]], code_evidence: list[dict[str, Any]]) -> dict[str, Any]:
    term_hits = find_label_terms(label_sources, ARCH_TERMS)
    policy: dict[str, Any] = {}
    for name, term in [
        ("uses_room_boundary", "boundary"),
        ("uses_wall", "wall"),
        ("uses_door", "door"),
        ("uses_window", "window"),
        ("uses_opening", "opening"),
        ("uses_floor", "floor"),
        ("uses_background", "background"),
    ]:
        has_label = bool(term_hits.get(term))
        has_code = any(term in json.dumps(item, ensure_ascii=False).lower() for item in code_evidence)
        policy[name] = True if has_label or has_code else "unknown"
    label_color_or_index = {}
    for term, hits in term_hits.items():
        if hits:
            label_color_or_index[term] = hits[:10]
    return {
        **policy,
        "source_files": sorted({item["file"] for item in code_evidence})[:40],
        "label_color_or_index": label_color_or_index,
    }


def infer_furniture_policy(label_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}
    for source, rows in label_sources.items():
        for row in rows:
            label = row.get("label")
            if isinstance(label, (dict, list)):
                label = json.dumps(label, ensure_ascii=False)
            if label is None:
                continue
            key = str(label).strip()
            if not key:
                continue
            classes.setdefault(key, {"label": key, "sources": [], "entries": []})
            classes[key]["sources"].append(source)
            if len(classes[key]["entries"]) < 3:
                classes[key]["entries"].append(row)
    return {
        "class_count": len(classes),
        "classes": sorted(classes.keys())[:120],
        "source_files": sorted({source for item in classes.values() for source in item["sources"]}),
        "label_color_or_index": {key: value["entries"] for key, value in list(classes.items())[:80]},
    }


def classify_non_core(label_sources: dict[str, list[dict[str, Any]]], code_evidence: list[dict[str, Any]]) -> dict[str, Any]:
    term_hits = find_label_terms(label_sources, NON_CORE_TERMS)
    out: dict[str, Any] = {}
    for key in ("door", "window", "curtain", "lamp", "ceiling lamp", "pendant lamp", "opening", "wall"):
        hits = term_hits.get(key, [])
        evidence = hits[:10]
        code_hits = [item for item in code_evidence if key in json.dumps(item, ensure_ascii=False).lower()][:8]
        role = "unknown"
        joined = json.dumps(evidence + code_hits, ensure_ascii=False).lower()
        if key in {"door", "window", "opening", "wall"}:
            if joined:
                role = "architecture_condition"
        elif "lamp" in key:
            role = "furniture_label" if hits else "unknown"
        elif key == "curtain":
            role = "architecture_condition" if hits else "unknown"
        out[key] = {"role": role, "evidence": evidence + code_hits}
    return out


def inspect_processed_outputs(root: Path) -> dict[str, Any]:
    candidates = sorted((root / "datasets").glob("**/Updated_Bottom_inst_anno.json"))[:12]
    label_maps = sorted((root / "datasets").glob("**/Updated_Bottom_label_map.png"))[:12]
    category_counts: dict[str, int] = {}
    door_window = False
    furniture_instances = False
    evidence = []
    for path in candidates[:5]:
        try:
            payload = load_json(path)
        except Exception as exc:  # noqa: BLE001
            evidence.append({"file": rel(path, root), "error": repr(exc)})
            continue
        entries = payload if isinstance(payload, list) else payload.get("instances") or payload.get("objects") or []
        if isinstance(entries, dict):
            entries = list(entries.values())
        sample = []
        for item in entries[:20] if isinstance(entries, list) else []:
            if not isinstance(item, dict):
                continue
            cat = str(item.get("category") or item.get("label") or item.get("class") or "")
            category_counts[cat] = category_counts.get(cat, 0) + 1
            text = json.dumps(item, ensure_ascii=False).lower()
            if "door" in text or "window" in text:
                door_window = True
            if any(k in item for k in ("bbox", "mask", "category", "orientation", "rotY")):
                furniture_instances = True
            if len(sample) < 5:
                sample.append({k: item.get(k) for k in ("category", "label", "bbox", "orientation_source", "rotY", "uid", "jid") if k in item})
        evidence.append({"file": rel(path, root), "sample_entries": sample})
    label_role = "mixed" if label_maps and door_window else "furniture_semantic" if label_maps else "unknown"
    inst_role = "mixed" if door_window else "furniture_instances" if furniture_instances else "unknown"
    return {
        "label_map_role": label_role,
        "inst_anno_role": inst_role,
        "door_window_in_inst_anno": door_window,
        "furniture_instances_in_inst_anno": furniture_instances,
        "label_map_candidates": [rel(path, root) for path in label_maps[:12]],
        "inst_anno_candidates": [rel(path, root) for path in candidates[:12]],
        "category_counts_head": sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:30],
        "evidence": evidence,
    }


def build_recommendation(arch_policy: dict[str, Any], non_core: dict[str, Any]) -> dict[str, Any]:
    anchors = []
    channels = ["room_boundary", "floor"]
    for item in ("wall", "door", "window", "opening"):
        key = f"uses_{item}"
        if arch_policy.get(key) is True:
            channels.append(item)
            anchors.append(item)
    return {
        "architecture_condition_channels": channels,
        "architecture_json_anchors": anchors,
        "furniture_palette_keep_core": ["bed", "wardrobe", "desk", "chair", "nightstand"],
        "accessory_or_ignore": ["curtain", "lamp", "ceiling_lamp", "pendant_lamp", "plants", "pillow", "decor"],
        "do_not_treat_as_furniture": ["door", "window", "opening", "wall", "floor", "background"],
        "category_mapping_updates": [
            "Map door/window/opening/wall to architecture anchors, not furniture entities.",
            "Keep lamp/curtain as accessory_or_ignore unless the LoReflection palette is explicitly expanded.",
            "Keep raw/reference/loreflection category fields for all parsed objects.",
        ],
        "converter_updates": [
            "Move door/window-like objects from Observed LoState furniture_instances to Architecture JSON anchors.",
            "Render door/window anchors in architecture condition image.",
            "Filter semantic furniture layout to core furniture palette unless accessory classes are explicitly enabled.",
            "Use SemLayoutDiff processed label maps only as policy/reference visualization, not raw geometry source.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", type=Path, required=True)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    label_sources = collect_metadata_labels(args.semlayoutdiff_root)
    code_files = [
        "configs/data_processing.yaml",
        "preprocess/scripts/data_processor.py",
        "preprocess/scripts/json_threed_future_dataset.py",
    ]
    code_evidence = source_rel_evidence(args.semlayoutdiff_root, code_files, ARCH_TERMS + NON_CORE_TERMS)
    arch_policy = infer_architecture_policy(label_sources, code_evidence)
    furniture_policy = infer_furniture_policy(label_sources)
    non_core_policy = classify_non_core(label_sources, code_evidence)
    processed_policy = inspect_processed_outputs(args.semlayoutdiff_root)
    recommendation = build_recommendation(arch_policy, non_core_policy)

    report = {
        "report_version": "semlayoutdiff-label-policy-v1",
        "paths": {
            "semlayoutdiff_root": args.semlayoutdiff_root.as_posix(),
            "prototype_root": args.prototype_root.as_posix(),
        },
        "file_status": file_status(args.semlayoutdiff_root),
        "architecture_condition_policy": arch_policy,
        "furniture_semantic_policy": furniture_policy,
        "non_core_object_policy": non_core_policy,
        "processed_output_policy": processed_policy,
        "recommended_loreflection_policy": recommendation,
        "safety": {
            "downloaded_data": False,
            "downloaded_models": False,
            "training_started": False,
            "full_conversion_started": False,
            "third_party_code_executed": False,
        },
    }
    write_json(args.output, report)
    if args.verbose:
        print(json.dumps({
            "architecture_condition_policy": arch_policy,
            "non_core_roles": {k: v["role"] for k, v in non_core_policy.items()},
            "furniture_class_count": furniture_policy["class_count"],
            "processed_label_map_role": processed_policy["label_map_role"],
            "output": args.output.as_posix(),
        }, ensure_ascii=False, indent=2))
    print(f"Wrote SemLayoutDiff label policy report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
