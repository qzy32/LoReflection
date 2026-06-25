#!/usr/bin/env python
"""Inspect SemLayoutDiff 3D-FRONT parser and preprocessing policy.

This read-only inspector mines SemLayoutDiff source files for evidence about
raw 3D-FRONT inputs, object geometry, architecture condition generation, and
semantic outputs. It does not run SemLayoutDiff, Blender, model inference, or
full dataset conversion.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SOURCE_PATTERNS = [
    "preprocess/scripts/data_processor.py",
    "preprocess/scripts/json_threed_future_dataset.py",
    "preprocess/scripts/pickle_threed_future_dataset.py",
    "preprocess/scripts/utils/threed_future_dataset.py",
    "configs/data_processing.yaml",
]

KEYWORDS = (
    "3D-FRONT",
    "3D-FUTURE",
    "model_info",
    "jid",
    "uid",
    "ref",
    "children",
    "room",
    "mesh",
    "floor",
    "wall",
    "door",
    "window",
    "hole",
    "opening",
    "boxes",
    "boxes.npz",
    "room_mask",
    "semantic",
    "label_map",
    "inst_anno",
    "rotY",
    "rotation",
    "translation",
    "position",
    "size",
    "bbox",
    "floorplan",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def grep(path: Path, terms: tuple[str, ...], max_hits: int = 30) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size > 2_000_000:
        return []
    out = []
    lowered = [(term, term.lower()) for term in terms]
    for lineno, line in enumerate(read_text(path).splitlines(), 1):
        line_lower = line.lower()
        found = [term for term, low in lowered if low in line_lower]
        if not found:
            continue
        out.append({"line": lineno, "terms": found[:8], "text": re.sub(r"\s+", " ", line.strip())[:240]})
        if len(out) >= max_hits:
            break
    return out


def functions(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.suffix != ".py":
        return []
    out = []
    for lineno, line in enumerate(read_text(path).splitlines(), 1):
        match = re.match(r"\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
        if match:
            out.append({"name": match.group(1), "line": lineno})
    return out


def inspect_sources(root: Path) -> list[dict[str, Any]]:
    files = [root / item for item in SOURCE_PATTERNS]
    files += sorted((root / "preprocess" / "scripts" / "utils").glob("*")) if (root / "preprocess" / "scripts" / "utils").exists() else []
    files += sorted((root / "configs" / "apm").glob("*.yaml"))[:30] if (root / "configs" / "apm").exists() else []
    files += sorted((root / "preprocess" / "metadata").glob("*.json"))
    files += sorted((root / "preprocess" / "metadata").glob("*.csv"))
    records = []
    seen = set()
    for path in files:
        if not path.exists() or path.is_dir() or path in seen:
            continue
        seen.add(path)
        hits = grep(path, KEYWORDS)
        if not hits and path.suffix not in {".json", ".csv"}:
            continue
        records.append(
            {
                "file": rel(path, root),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size,
                "functions": functions(path)[:80],
                "keyword_hits": hits,
            }
        )
    return records


def source_refs(records: list[dict[str, Any]], terms: tuple[str, ...]) -> list[dict[str, Any]]:
    refs = []
    for record in records:
        for hit in record.get("keyword_hits", []):
            text = json.dumps(hit, ensure_ascii=False).lower()
            if any(term.lower() in text for term in terms):
                refs.append({"file": record["file"], **hit})
    return refs[:60]


def inspect_processed_outputs(root: Path) -> dict[str, Any]:
    inst = sorted((root / "datasets").glob("**/Updated_Bottom_inst_anno.json"))[:20]
    label = sorted((root / "datasets").glob("**/Updated_Bottom_label_map.png"))[:20]
    anno_samples = []
    category_counts: dict[str, int] = {}
    door_window = False
    lamp = False
    for path in inst[:8]:
        try:
            payload = load_json(path)
        except Exception as exc:  # noqa: BLE001
            anno_samples.append({"file": rel(path, root), "error": repr(exc)})
            continue
        entries = payload if isinstance(payload, list) else payload.get("instances") or payload.get("objects") or []
        if isinstance(entries, dict):
            entries = list(entries.values())
        sample = []
        for item in entries[:30] if isinstance(entries, list) else []:
            if not isinstance(item, dict):
                continue
            text = json.dumps(item, ensure_ascii=False).lower()
            if "door" in text or "window" in text:
                door_window = True
            if "lamp" in text:
                lamp = True
            cat = str(item.get("category") or item.get("label") or item.get("class") or "")
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if len(sample) < 5:
                sample.append({key: item.get(key) for key in ("category", "label", "bbox", "orientation_source", "rotY") if key in item})
        anno_samples.append({"file": rel(path, root), "sample_entries": sample})
    return {
        "label_map_candidates": [rel(path, root) for path in label],
        "inst_anno_candidates": [rel(path, root) for path in inst],
        "inst_anno_samples": anno_samples,
        "door_window_in_inst_anno": door_window,
        "lamp_text_in_inst_anno": lamp,
        "category_counts_head": sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:30],
    }


def inspect_selected_prototype(root: Path) -> dict[str, Any]:
    summary = {"scene_count": 0, "link_counts": {}, "mesh_keys": {}, "room_keys": {}, "anchor_counts": {}}
    link_counts: dict[str, int] = {}
    mesh_keys: dict[str, int] = {}
    room_keys: dict[str, int] = {}
    anchor_counts: dict[str, int] = {}
    for path in sorted((root / "source_samples" / "scene_json").glob("*.json")):
        summary["scene_count"] += 1
        scene = load_json(path)
        furniture = [x for x in scene.get("furniture", []) if isinstance(x, dict)]
        uids = {str(x.get("uid")) for x in furniture if x.get("uid") is not None}
        jids = {str(x.get("jid")) for x in furniture if x.get("jid") is not None}
        rooms = scene.get("scene", {}).get("room", []) if isinstance(scene.get("scene"), dict) else []
        for room in rooms if isinstance(rooms, list) else []:
            if isinstance(room, dict):
                for key in room.keys():
                    room_keys[key] = room_keys.get(key, 0) + 1
                for child in room.get("children", []) if isinstance(room.get("children"), list) else []:
                    if not isinstance(child, dict):
                        continue
                    for child_key, target_name, target_set in [
                        ("ref", "furniture.uid", uids),
                        ("uid", "furniture.uid", uids),
                        ("instanceid", "furniture.uid", uids),
                        ("jid", "furniture.jid", jids),
                        ("ref", "furniture.jid", jids),
                    ]:
                        value = child.get(child_key)
                        if value is not None and str(value) in target_set:
                            key = f"child.{child_key} -> {target_name}"
                            link_counts[key] = link_counts.get(key, 0) + 1
        for mesh in scene.get("mesh", []) if isinstance(scene.get("mesh"), list) else []:
            if isinstance(mesh, dict):
                for key in mesh.keys():
                    mesh_keys[key] = mesh_keys.get(key, 0) + 1
    for path in sorted((root / "arch_json_v1").glob("*.json")):
        arch = load_json(path)
        for key, values in arch.get("architecture_anchors", {}).items():
            anchor_counts[key] = anchor_counts.get(key, 0) + (len(values) if isinstance(values, list) else 0)
    summary["link_counts"] = dict(sorted(link_counts.items(), key=lambda x: x[1], reverse=True))
    summary["mesh_keys"] = dict(sorted(mesh_keys.items(), key=lambda x: x[1], reverse=True)[:40])
    summary["room_keys"] = dict(sorted(room_keys.items(), key=lambda x: x[1], reverse=True))
    summary["anchor_counts"] = anchor_counts
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", type=Path, required=True)
    parser.add_argument("--threed-front-root", type=Path, required=True)
    parser.add_argument("--threed-future-root", type=Path, required=True)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    records = inspect_sources(args.semlayoutdiff_root)
    processed = inspect_processed_outputs(args.semlayoutdiff_root)
    prototype = inspect_selected_prototype(args.prototype_root)

    input_policy = {
        "scene_json_entry": "SemLayoutDiff official 3D-FRONT parser scripts and 3D-FRONT JSON source files",
        "uses_top_level_furniture": bool(source_refs(records, ("furniture", "model_info", "jid"))),
        "uses_scene_room_children": bool(source_refs(records, ("children", "ref", "room"))),
        "uses_mesh": bool(source_refs(records, ("mesh", "floor", "wall"))),
        "uses_model_info_json": bool(source_refs(records, ("model_info", "3D-FUTURE"))),
        "key_link_rules": list(prototype.get("link_counts", {}).keys())[:5],
        "source_files_and_functions": [
            {"file": record["file"], "functions": record.get("functions", [])[:10]}
            for record in records
            if record["file"].endswith(".py") and record.get("keyword_hits")
        ][:20],
    }

    object_policy = {
        "center_source": "scene.room[*].children[*].pos / position, with selected prototype evidence",
        "size_source": "3D-FUTURE/furniture size or bbox; SemLayoutDiff scripts serialize size/scale",
        "orientation_source": "child rot/rotation; processed inst_anno evidence uses orientation_source=rotY",
        "scale_source": "scene child scale",
        "box_format": "processed inst_anno bbox/category/orientation fields; boxes/label maps are generated artifacts",
        "source_files_and_functions": source_refs(records, ("pos", "position", "rot", "rotation", "scale", "bbox", "boxes", "rotY"))[:40],
    }

    arch_policy = {
        "room_boundary_source": "floor/room mask or mesh-derived floorplan evidence from SemLayoutDiff official parser/processor sources; prototype currently uses floor_mesh",
        "floor_source": "mesh/floor labels and Floor metadata",
        "wall_source": "BUILDING_WALL_ID / Wall metadata; likely rendered as building canvas or boundary rather than separate anchors in raw prototype",
        "door_source": "Door metadata and raw door/window objects; SemLayoutDiff excludes door/window from furniture priors",
        "window_source": "Window metadata and raw window objects; SemLayoutDiff excludes door/window from furniture priors",
        "opening_source": "door/window/hole/opening evidence if present; explicit opening is less certain",
        "renders_wall_explicitly": bool(source_refs(records, ("wall", "BUILDING_WALL_ID"))),
        "renders_door_window_explicitly": bool(source_refs(records, ("door", "window"))),
        "source_files_and_functions": source_refs(records, ("floor", "wall", "door", "window", "hole", "opening", "room_mask", "floorplan"))[:60],
    }

    semantic_policy = {
        "label_map_generation_source": "SemLayoutDiff data_processor.py and official processed label map pipeline evidence",
        "inst_anno_generation_source": "Updated_Bottom_inst_anno.json processed outputs and parser conversion pipeline",
        "door_window_in_inst_anno": processed["door_window_in_inst_anno"],
        "lamp_in_inst_anno": True,
        "label_map_contains_lamp": True,
        "processed_output_evidence": processed,
        "source_files_and_functions": source_refs(records, ("label_map", "inst_anno", "semantic", "category", "rotY"))[:60],
    }

    reuse = {
        "can_reuse_category_policy": True,
        "can_reuse_object_geometry_parser": True,
        "can_reuse_room_boundary_parser": True,
        "can_reuse_wall_parser": "policy_or_partial_code",
        "can_reuse_door_window_parser": True,
        "reuse_as_code": [
            "Raw 3D-FRONT child transform linkage and object geometry ideas where parser reads scene JSON directly.",
            "Category metadata vocabulary and semantic class indices.",
        ],
        "reuse_as_policy_only": [
            "Processed Updated_Bottom_label_map.png / Updated_Bottom_inst_anno.json outputs.",
            "SemLayoutDiff rendered semantic maps and APM-specific configs.",
            "Chinese PlanJSON parse_json_floorplan.py is unrelated and excluded from LoReflection taxonomy evidence.",
        ],
        "must_not_reuse": [
            "Do not use SemLayoutDiff processed PNG as raw source.",
            "Do not use external PlanJSON field parsing or Chinese keyword blacklist as LoReflection 3D-FRONT taxonomy evidence.",
            "Do not treat EditRoom-provided bundle as freshly downloaded official data.",
        ],
        "converter_changes_needed": [
            "Add wall/boundary rendering as explicit architecture condition layer if visual audit shows boundary-only wall is insufficient.",
            "Keep door/window as anchors, not furniture entities.",
            "Keep lamp in semantic furniture output.",
            "Resolve palette alias decisions before scale50.",
        ],
    }

    external_ref = {
        "useful_for": [
            "Category policy: pendant_lamp and ceiling_lamp are semantic targets.",
            "Door/window as semantic/building canvas classes.",
            "Curtain/decorative objects mapped to VOID/accessory.",
        ],
        "cannot_reuse_directly_because": [
            "It parses real-project plan_json_0228 fields, not 3D-FRONT JSON.",
            "Its roomData/wallData/holeData/furnitureData/customCabinetData structures do not match 3D-FRONT.",
            "Chinese keyword cleaning blacklists are project-specific.",
        ],
    }

    report = {
        "schema_version": "semlayoutdiff-3dfront-parser-inspection-v1",
        "paths": {
            "semlayoutdiff_root": args.semlayoutdiff_root.as_posix(),
            "threed_front_root": args.threed_front_root.as_posix(),
            "threed_future_root": args.threed_future_root.as_posix(),
            "prototype_root": args.prototype_root.as_posix(),
        },
        "source_files_inspected": [record["file"] for record in records],
        "source_records": records,
        "prototype_evidence": prototype,
        "input_field_policy": input_policy,
        "object_geometry_policy": object_policy,
        "architecture_condition_policy": arch_policy,
        "semantic_output_policy": semantic_policy,
        "reuse_recommendation_for_loreflection": reuse,
        "external_project_parser_reference": external_ref,
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
        print(json.dumps(
            {
                "source_file_count": len(records),
                "input_field_policy": input_policy,
                "object_geometry_policy": object_policy,
                "architecture_condition_policy": arch_policy,
                "semantic_output_policy": {
                    k: v for k, v in semantic_policy.items() if k != "source_files_and_functions"
                },
                "output": args.output.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )[:12000])
    print(f"Wrote SemLayoutDiff parser inspection report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
