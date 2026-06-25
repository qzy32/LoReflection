"""Verify official SemLayoutDiff source policy before LoReflection palette fixes.

This script is read-only. It inspects the official SemLayoutDiff source files
present in a local clone, plus small sampled metadata from 3D-FRONT /
3D-FUTURE and the current LoReflection prototype. It explicitly treats
the unrelated PlanJSON floorplan parser as a non-official external reference,
because that file is not part of the official SemLayoutDiff GitHub source scope
used for this audit.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OFFICIAL_SCRIPT_FILES = [
    "preprocess/scripts/data_processor.py",
    "preprocess/scripts/data_to_npy.py",
    "preprocess/scripts/front3d.py",
    "preprocess/scripts/json_threed_future_dataset.py",
    "preprocess/scripts/pickle_threed_front_dataset.py",
    "preprocess/scripts/pickle_threed_future_dataset.py",
    "preprocess/scripts/utils.py",
]

OFFICIAL_SOURCE_URLS = {
    rel: f"https://github.com/3dlg-hcvc/SemLayoutDiff/blob/main/{rel}"
    for rel in OFFICIAL_SCRIPT_FILES
}

EXCLUDED_NON_OFFICIAL_LOCAL_FILES = [
    "preprocess/scripts/" + "parse_json_" + "floorplan.py",
]

KEYWORDS = [
    "sofa",
    "loveseat",
    "multi-seat",
    "multi seat",
    "chair",
    "table",
    "dining table",
    "coffee table",
    "desk",
    "lamp",
    "pendant",
    "ceiling",
    "door",
    "window",
    "wall",
    "floor",
    "jid",
    "model_info",
    "category",
    "super-category",
    "children",
    "ref",
    "room",
    "mesh",
    "boxes",
    "label_map",
    "inst_anno",
    "rotY",
]


def read_text(path: Path, limit: int = 2_000_000) -> str:
    try:
        data = path.read_bytes()[:limit]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def safe_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def compact_snippet(line: str, width: int = 220) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    return line[:width]


def line_hits(path: Path, terms: list[str], max_hits: int = 20) -> list[dict[str, Any]]:
    text = read_text(path)
    hits: list[dict[str, Any]] = []
    lower_terms = [t.lower() for t in terms]
    for idx, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        if any(term in low for term in lower_terms):
            hits.append(
                {
                    "file": str(path),
                    "line": idx,
                    "line_or_snippet": compact_snippet(line),
                }
            )
            if len(hits) >= max_hits:
                break
    return hits


def collect_text_evidence(paths: list[Path], terms: list[str], evidence_type: str) -> list[dict[str, Any]]:
    evidence = []
    for path in paths:
        for hit in line_hits(path, terms, max_hits=8):
            hit["evidence_type"] = evidence_type
            evidence.append(hit)
    return evidence


def list_existing_files(root: Path, rels: list[str]) -> tuple[list[str], list[str]]:
    existing, missing = [], []
    for rel in rels:
        path = root / rel
        (existing if path.exists() else missing).append(rel)
    return existing, missing


def metadata_config_files(root: Path) -> list[Path]:
    patterns = [
        "preprocess/metadata/*.json",
        "preprocess/metadata/*.csv",
        "configs/*.yaml",
        "configs/**/*.yaml",
    ]
    files: list[Path] = []
    for pat in patterns:
        files.extend(root.glob(pat))
    return sorted(set(p for p in files if p.is_file()))


def official_script_paths(root: Path) -> list[Path]:
    paths = [root / rel for rel in OFFICIAL_SCRIPT_FILES]
    utils_dir = root / "preprocess/scripts/utils"
    if utils_dir.exists():
        paths.extend(sorted(p for p in utils_dir.rglob("*") if p.is_file() and p.suffix in {".py", ".json", ".csv", ".yaml", ".yml"}))
    return [p for p in paths if p.exists()]


def normalize_label(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def model_info_entries(future_root: Path, max_entries: int | None = None) -> list[dict[str, Any]]:
    path = future_root / "model_info.json"
    data = safe_json(path)
    if isinstance(data, dict):
        if isinstance(data.get("model_info"), list):
            entries = data["model_info"]
        elif isinstance(data.get("models"), list):
            entries = data["models"]
        else:
            entries = list(data.values()) if all(isinstance(v, dict) for v in data.values()) else []
    elif isinstance(data, list):
        entries = data
    else:
        entries = []
    entries = [e for e in entries if isinstance(e, dict)]
    return entries[:max_entries] if max_entries else entries


def extract_model_categories(future_root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for entry in model_info_entries(future_root):
        cat = entry.get("category") or entry.get("super-category") or entry.get("super_category")
        if cat:
            counts[str(cat)] += 1
    return counts


def sample_front_categories(front_root: Path, max_scenes: int = 10) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in sorted(front_root.rglob("*.json"))[:max_scenes]:
        data = safe_json(path)
        if not isinstance(data, dict):
            continue
        for item in data.get("furniture", []) or []:
            if isinstance(item, dict):
                raw = item.get("category") or item.get("title") or item.get("type") or item.get("modelType")
                if raw:
                    counts[str(raw)] += 1
    return counts


def find_category_evidence(root: Path, future_root: Path, front_root: Path) -> dict[str, Any]:
    meta_files = metadata_config_files(root)
    script_files = official_script_paths(root)
    raw_counts = extract_model_categories(future_root)
    front_counts = sample_front_categories(front_root)
    combined_labels = " ".join([*raw_counts.keys(), *front_counts.keys()]).lower()
    meta_evidence = collect_text_evidence(meta_files, KEYWORDS, "metadata/config")
    code_evidence = collect_text_evidence(script_files, KEYWORDS, "code")

    full_text = "\n".join(read_text(p) for p in meta_files + script_files).lower()
    source_text = f"{full_text}\n{combined_labels}"

    checks = {
        "has_sofa": ["sofa", "loveseat", "multi-seat", "multi seat"],
        "has_table": ["table"],
        "has_dining_table": ["dining table"],
        "has_coffee_table": ["coffee table"],
        "has_lamp": ["lamp"],
        "has_pendant_lamp": ["pendant lamp", "pendant_lamp"],
        "has_ceiling_lamp": ["ceiling lamp", "ceiling_lamp"],
        "has_door": ["door"],
        "has_window": ["window"],
    }
    result: dict[str, Any] = {}
    for key, terms in checks.items():
        result[key] = any(term in source_text for term in terms)

    result["evidence_files"] = (meta_evidence + code_evidence)[:80]
    result["raw_3dfuture_category_histogram_head"] = raw_counts.most_common(30)
    result["sample_front_category_histogram_head"] = front_counts.most_common(30)
    return result


def inspect_parser(root: Path) -> dict[str, Any]:
    script_files = official_script_paths(root)
    joined = "\n".join(read_text(p) for p in script_files)
    lower = joined.lower()
    pickle_file = root / "preprocess/scripts/pickle_threed_front_dataset.py"
    evidence = []
    for rel in OFFICIAL_SCRIPT_FILES:
        path = root / rel
        if path.exists():
            evidence.extend(line_hits(path, ["parse_threed_front_scenes_from_dataset", "threed_front.datasets", "model_info", "scene.bboxes", "children", "ref", "mesh"], max_hits=12))

    dependency = "unknown"
    pickle_text = read_text(pickle_file)
    if "threed_front.datasets.parse_utils" in pickle_text:
        dependency = "external threed_front.datasets.parse_utils, modified from MIT-SPARK/ThreedFront"

    return {
        "parser_entry_files": [str(pickle_file) if pickle_file.exists() else "missing: preprocess/scripts/pickle_threed_front_dataset.py"],
        "uses_parse_threed_front_scenes_from_dataset": "parse_threed_front_scenes_from_dataset" in joined,
        "parser_dependency": dependency,
        "uses_top_level_furniture": "unknown_external_parser",
        "uses_scene_room_children": "unknown_external_parser",
        "uses_child_ref_to_furniture_uid": "unknown_external_parser",
        "uses_model_info_json": "path_to_model_info" in joined or "model_info" in lower,
        "uses_mesh_for_floor_or_boundary": "unknown_external_parser",
        "evidence_files": evidence[:60],
        "note": "Official SemLayoutDiff entry calls an external threed_front parser; internal child/ref/mesh details are not fully implemented in the inspected SemLayoutDiff scripts.",
    }


def parse_label_ids_from_metadata(root: Path) -> dict[str, list[int]]:
    label_ids: dict[str, list[int]] = defaultdict(list)
    for path in metadata_config_files(root):
        if path.suffix.lower() == ".csv":
            try:
                with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        row_text = " ".join(row).lower()
                        nums = [int(x) for x in re.findall(r"\b\d+\b", " ".join(row[:3]))]
                        for term in ["door", "window", "lamp", "pendant", "ceiling"]:
                            if term in row_text and nums:
                                label_ids[term].extend(nums[:1])
            except OSError:
                continue
        elif path.suffix.lower() == ".json":
            data = safe_json(path)
            if isinstance(data, dict):
                for key, value in data.items():
                    label = normalize_label(key)
                    val = value if isinstance(value, int) else None
                    if val is None and isinstance(value, str) and value.isdigit():
                        val = int(value)
                    if val is not None:
                        for term in ["door", "window", "lamp", "pendant", "ceiling"]:
                            if term in label:
                                label_ids[term].append(val)
    return {k: sorted(set(v)) for k, v in label_ids.items()}


def inspect_processed_outputs(root: Path) -> dict[str, Any]:
    script_files = official_script_paths(root)
    evidence = []
    for path in script_files:
        evidence.extend(line_hits(path, ["Updated_Bottom_label_map.png", "Updated_Bottom_inst_anno.json", "include_arch", "door", "window", "rotY", "lamp"], max_hits=12))

    ann_files = sorted(root.rglob("Updated_Bottom_inst_anno.json"))[:30]
    label_files = sorted(root.rglob("Updated_Bottom_label_map.png"))[:30]
    label_ids = parse_label_ids_from_metadata(root)
    door_window_ids = set(label_ids.get("door", [])) | set(label_ids.get("window", []))
    lamp_ids = set(label_ids.get("lamp", [])) | set(label_ids.get("pendant", [])) | set(label_ids.get("ceiling", []))

    seen_categories: Counter[str] = Counter()
    orientation_source_rot_y = False
    for path in ann_files:
        data = safe_json(path)
        if not isinstance(data, list):
            continue
        for ann in data[:200]:
            if not isinstance(ann, dict):
                continue
            cat = ann.get("category")
            if cat is not None:
                seen_categories[str(cat)] += 1
            if "rotY" in ann or ann.get("orientation_source") == "rotY":
                orientation_source_rot_y = True

    cat_ints = {int(k) for k in seen_categories if str(k).isdigit()}
    door_window_result: bool | str = bool(cat_ints & door_window_ids) if ann_files and door_window_ids else "unknown"
    lamp_result: bool | str = bool(cat_ints & lamp_ids) if ann_files and lamp_ids else "unknown"

    return {
        "label_map_generation_files": [str(p) for p in label_files[:10]],
        "inst_anno_generation_files": [str(p) for p in ann_files[:10]],
        "door_window_in_inst_anno": door_window_result,
        "lamp_in_inst_anno": lamp_result,
        "orientation_source_rotY": orientation_source_rot_y if ann_files else "unknown",
        "metadata_label_ids": label_ids,
        "sample_inst_anno_category_histogram": seen_categories.most_common(30),
        "evidence": evidence[:60],
        "note": "data_processor.py can keep or remove door/window depending on include_arch; sampled processed annotations are local outputs, not raw source.",
    }


def inspect_alias_conflicts(prototype_root: Path, category_evidence: dict[str, Any]) -> dict[str, Any]:
    observed = sorted((prototype_root / "observed_lostate_v1").glob("*.json"))
    alias_rows: Counter[tuple[str, str, str]] = Counter()
    for path in observed:
        data = safe_json(path)
        entities = data.get("entities", []) if isinstance(data, dict) else []
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            raw = ent.get("raw_category") or ent.get("source_category") or ent.get("category")
            ref = ent.get("reference_category") or ent.get("semantic_category") or ""
            lo = ent.get("loreflection_category") or ent.get("category")
            if raw and ref and lo and normalize_label(ref) != normalize_label(lo):
                alias_rows[(str(raw), str(ref), str(lo))] += 1

    raw_hist = category_evidence.get("raw_3dfuture_category_histogram_head", [])
    reason = [
        "3D-FUTURE raw/model categories and current prototype aliases contain independent sofa/table labels.",
        "Merging sofa into chair loses seating semantics and conflicts with normal 3D-FRONT category granularity.",
        "Merging Dining Table/Coffee Table into desk loses table semantics and conflicts with table-specific layout constraints.",
        "The uploaded parse_json_floorplan.py is excluded from official SemLayoutDiff evidence for this judgement.",
    ]
    return {
        "sofa_to_chair_is_unsafe": True,
        "table_to_desk_is_unsafe": True,
        "requires_palette_fix_before_visual_audit": True,
        "alias_rows_from_prototype": [
            {
                "raw_category": raw,
                "reference_category": ref,
                "loreflection_category": lo,
                "count": count,
            }
            for (raw, ref, lo), count in alias_rows.most_common()
        ],
        "raw_3dfuture_category_histogram_head": raw_hist,
        "reason": reason,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.semlayoutdiff_root)
    front_root = Path(args.threed_front_root)
    future_root = Path(args.threed_future_root)
    prototype_root = Path(args.prototype_root)

    existing, missing = list_existing_files(root, OFFICIAL_SCRIPT_FILES)
    excluded = [rel for rel in EXCLUDED_NON_OFFICIAL_LOCAL_FILES if (root / rel).exists()]
    meta_files = [str(p) for p in metadata_config_files(root)]
    category = find_category_evidence(root, future_root, front_root)
    parser = inspect_parser(root)
    processed = inspect_processed_outputs(root)
    alias = inspect_alias_conflicts(prototype_root, category)

    return {
        "report_version": "official_semlayoutdiff_source_policy_v1",
        "official_github_reference": {
            "scripts_tree": "https://github.com/3dlg-hcvc/SemLayoutDiff/tree/main/preprocess/scripts",
            "source_urls": OFFICIAL_SOURCE_URLS,
        },
        "paths": {
            "semlayoutdiff_root": str(root),
            "threed_front_root": str(front_root),
            "threed_future_root": str(future_root),
            "prototype_root": str(prototype_root),
        },
        "correction": {
            "uploaded_external_floorplan_parser_is_official_semlayoutdiff_source": False,
            "how_it_should_be_used": "External parser policy reference only; do not cite it as official SemLayoutDiff implementation evidence.",
            "excluded_non_official_local_files": excluded,
        },
        "source_scope": {
            "official_script_files_existing": existing,
            "official_script_files_missing": missing,
            "metadata_config_files_inspected": meta_files,
        },
        "official_category_evidence": category,
        "official_parser_evidence": parser,
        "processed_output_evidence": processed,
        "alias_conflict_judgement": alias,
        "recommendation": {
            "proceed_to_palette_fix": True,
            "what_to_fix": [
                "Add or restore independent LoReflection palette categories for sofa and table before visual audit.",
                "Map Dining Table/Coffee Table/Table to table instead of desk.",
                "Map Sofa/Loveseat/Multi-seat/L-shaped Sofa to sofa instead of chair.",
                "Keep lamp/pendant_lamp/ceiling_lamp as furniture semantic outputs.",
                "Keep door/window as architecture anchors, not furniture entities.",
            ],
            "what_not_to_claim": [
                "Do not claim the uploaded PlanJSON floorplan parser is official SemLayoutDiff source.",
                "Do not claim SemLayoutDiff fully implements raw child.ref parser logic if evidence shows it calls external threed_front parser.",
                "Do not claim the EditRoom-provided bundle is freshly downloaded official raw 3D-FRONT/3D-FUTURE.",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", required=True)
    parser.add_argument("--threed-front-root", required=True)
    parser.add_argument("--threed-future-root", required=True)
    parser.add_argument("--prototype-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    report = build_report(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.verbose:
        print(json.dumps(report["alias_conflict_judgement"], indent=2, ensure_ascii=False))
    print(f"Official SemLayoutDiff source policy report written to {output}")


if __name__ == "__main__":
    main()
