#!/usr/bin/env python
"""Compare two bounded prototypes for semantic equivalence after refactors."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_STATS = {
    "semantic_drawn_count": 90,
    "core_furniture_count": 72,
    "lighting_count": 18,
    "sofa_count": 5,
    "table_count": 10,
    "lamp_count": 18,
    "door_window_entities": 0,
    "wall_entities": 0,
    "unsafe_alias_count": 0,
    "sofa_to_chair_count": 0,
    "table_to_desk_count": 0,
    "core_unknown_count": 0,
    "lamp_unknown_count": 0,
    "core_missing_transform_count": 0,
    "lamp_missing_transform_count": 0,
    "boundary_polygon_valid": 5,
    "architecture_condition_has_boundary_contour": 5,
    "derived_wall_segment_count_total": 20,
    "against_wall_reference_source_missing": 0,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sample_map(root: Path) -> dict[str, dict[str, Any]]:
    manifest = load_json(root / "manifest.json")
    return {sample["scene_id"]: sample for sample in manifest.get("samples", [])}


def canonical_entities(observed: dict[str, Any]) -> list[dict[str, Any]]:
    keep = []
    for entity in observed.get("furniture_instances", []):
        keep.append(
            {
                "instance_id": entity.get("instance_id"),
                "category": entity.get("category"),
                "bbox_px": entity.get("bbox_px"),
                "area_px": entity.get("area_px"),
                "source_jid": entity.get("source_jid"),
                "center": entity.get("center"),
                "size": entity.get("size"),
                "orientation": entity.get("orientation"),
                "footprint": entity.get("footprint"),
                "mapping_status": entity.get("mapping_status"),
                "raw_category": entity.get("raw_category"),
                "raw_super_category": entity.get("raw_super_category"),
                "raw_title": entity.get("raw_title"),
                "reference_category": entity.get("reference_category"),
                "loreflection_category": entity.get("loreflection_category"),
                "transform_source": entity.get("transform_source"),
                "size_source": entity.get("size_source"),
                "is_lamp": entity.get("is_lamp"),
                "palette_alias_used": entity.get("palette_alias_used"),
            }
        )
    return sorted(keep, key=lambda item: str(item.get("instance_id")))


def canonical_architecture(arch: dict[str, Any]) -> dict[str, Any]:
    anchors = arch.get("architecture_anchors", {})
    return {
        "room_type": arch.get("room_type"),
        "coordinate_system": arch.get("coordinate_system"),
        "boundary": arch.get("boundary"),
        "boundary_source": arch.get("boundary_source"),
        "derived_wall_segments": arch.get("metadata", {}).get("derived_wall_segments", []),
        "doors": anchors.get("doors", []),
        "windows": anchors.get("windows", []),
        "openings": anchors.get("openings", []),
        "condition_metadata": arch.get("architecture_condition_metadata", {}),
    }


def category_stats(root: Path) -> dict[str, Any]:
    hist = Counter()
    groups = Counter()
    door_window = 0
    wall = 0
    for path in sorted((root / "observed_lostate_v1").glob("*.json")):
        observed = load_json(path)
        for entity in observed.get("furniture_instances", []):
            cat = str(entity.get("category") or "")
            hist[cat] += 1
            groups[str(entity.get("semantic_group") or ("lighting" if entity.get("is_lamp") else "core_furniture"))] += 1
            labels = {cat.lower(), str(entity.get("reference_category") or "").lower(), str(entity.get("raw_category") or "").lower()}
            if labels & {"door", "window"}:
                door_window += 1
            if "wall" in labels:
                wall += 1
    lamp_count = sum(hist[k] for k in ["lamp", "pendant_lamp", "ceiling_lamp", "floor_lamp"])
    return {
        "category_histogram": dict(hist.most_common()),
        "semantic_group_histogram": dict(groups.most_common()),
        "sofa_count": hist.get("sofa", 0),
        "table_count": hist.get("table", 0),
        "lamp_count": lamp_count,
        "door_window_entities": door_window,
        "wall_entities": wall,
    }


def compare(old_root: Path, new_root: Path) -> dict[str, Any]:
    old_samples = sample_map(old_root)
    new_samples = sample_map(new_root)
    failures: list[str] = []
    image_results = []
    entity_results = []
    architecture_results = []
    if sorted(old_samples) != sorted(new_samples):
        failures.append("scene ids differ")

    for scene_id in sorted(set(old_samples) & set(new_samples)):
        old_sample = old_samples[scene_id]
        new_sample = new_samples[scene_id]
        for key in ["architecture_condition", "semantic_layout"]:
            old_hash = sha256(old_root / old_sample[key])
            new_hash = sha256(new_root / new_sample[key])
            same = old_hash == new_hash
            if not same:
                failures.append(f"{scene_id}: {key} hash differs")
            image_results.append({"scene_id": scene_id, "kind": key, "identical": same, "old_sha256": old_hash, "new_sha256": new_hash})

        old_obs = load_json(old_root / old_sample["observed_lostate"])
        new_obs = load_json(new_root / new_sample["observed_lostate"])
        old_entities = canonical_entities(old_obs)
        new_entities = canonical_entities(new_obs)
        same_entities = old_entities == new_entities
        if not same_entities:
            failures.append(f"{scene_id}: observed entity canonical fields differ")
        entity_results.append({"scene_id": scene_id, "identical": same_entities, "old_count": len(old_entities), "new_count": len(new_entities)})

        old_arch = canonical_architecture(load_json(old_root / old_sample["architecture_json"]))
        new_arch = canonical_architecture(load_json(new_root / new_sample["architecture_json"]))
        same_arch = old_arch == new_arch
        if not same_arch:
            failures.append(f"{scene_id}: architecture canonical geometry differs")
        architecture_results.append({"scene_id": scene_id, "identical": same_arch})

    old_conv = load_json(old_root / "reports" / "conversion_report.json")
    new_conv = load_json(new_root / "reports" / "conversion_report.json")
    new_alias = load_json(new_root / "reports" / "palette_alias_audit.json")
    new_arch_val = load_json(new_root / "reports" / "architecture_condition_validation.json")
    new_stats = category_stats(new_root)
    semantic = new_conv.get("semantic_layout", {})
    transform = new_conv.get("transform_extraction", {})
    regression = {
        "semantic_drawn_count": semantic.get("semantic_drawn_count"),
        "core_furniture_count": semantic.get("furniture_kept_by_semantic_group", {}).get("core_furniture", semantic.get("core_furniture_kept")),
        "lighting_count": semantic.get("furniture_kept_by_semantic_group", {}).get("lighting", semantic.get("lamp_kept")),
        "sofa_count": new_stats["sofa_count"],
        "table_count": new_stats["table_count"],
        "lamp_count": new_stats["lamp_count"],
        "door_window_entities": new_stats["door_window_entities"],
        "wall_entities": new_stats["wall_entities"],
        "unsafe_alias_count": new_alias.get("unsafe_alias_count"),
        "sofa_to_chair_count": new_alias.get("sofa_to_chair_count"),
        "table_to_desk_count": new_alias.get("table_to_desk_count"),
        "core_unknown_count": semantic.get("core_unknown_count"),
        "lamp_unknown_count": semantic.get("lamp_unknown_count"),
        "core_missing_transform_count": transform.get("core_missing_transform_count"),
        "lamp_missing_transform_count": transform.get("lamp_missing_transform_count"),
        "boundary_polygon_valid": new_arch_val.get("boundary_polygon_valid_count"),
        "architecture_condition_has_boundary_contour": new_arch_val.get("architecture_condition_has_boundary_contour_count"),
        "derived_wall_segment_count_total": new_arch_val.get("derived_wall_segment_count_total"),
        "against_wall_reference_source_missing": new_arch_val.get("against_wall_reference_source_summary", {}).get("missing", 0),
    }
    for key, expected in EXPECTED_STATS.items():
        if regression.get(key) != expected:
            failures.append(f"{key} expected {expected}, got {regression.get(key)}")

    return {
        "schema_version": "prototype-semantic-equivalence-v1",
        "old_root": old_root.as_posix(),
        "new_root": new_root.as_posix(),
        "scene_ids": sorted(set(old_samples) & set(new_samples)),
        "architecture_condition_images_identical": all(r["identical"] for r in image_results if r["kind"] == "architecture_condition"),
        "semantic_layout_images_identical": all(r["identical"] for r in image_results if r["kind"] == "semantic_layout"),
        "entity_geometry_identical": all(r["identical"] for r in entity_results),
        "architecture_geometry_identical": all(r["identical"] for r in architecture_results),
        "category_histograms_identical": category_stats(old_root)["category_histogram"] == new_stats["category_histogram"],
        "image_results": image_results,
        "entity_results": entity_results,
        "architecture_results": architecture_results,
        "regression_stats": regression,
        "old_conversion_summary": old_conv.get("semantic_layout", {}),
        "new_conversion_summary": new_conv.get("semantic_layout", {}),
        "failures": failures,
        "status": "failed" if failures else "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-root", type=Path, required=True)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = compare(args.old_root, args.new_root)
    write_json(args.output, report)
    if report["failures"]:
        print(f"Prototype semantic equivalence failed: {report['failures']}")
        return 1 if args.strict else 0
    print("Prototype semantic equivalence passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
