#!/usr/bin/env python
"""Validate architecture-condition geometry for a bounded LoReflection package.

The validator enforces the R5 policy:
- wall is an immutable architecture reference, not furniture;
- raw wall anchors are optional;
- boundary-derived wall segments are required when explicit wall anchors are
  absent;
- door/window/wall must not appear as Observed LoState furniture entities.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def is_png(path: Path) -> bool:
    try:
        return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def polygon_area(points: list[list[float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for idx, p0 in enumerate(points):
        p1 = points[(idx + 1) % len(points)]
        area += float(p0[0]) * float(p1[1]) - float(p1[0]) * float(p0[1])
    return abs(area) * 0.5


def inspect_scene(package_root: Path, sample: dict[str, Any]) -> dict[str, Any]:
    scene_id = str(sample.get("scene_id", "unknown"))
    arch_path = package_root / str(sample.get("architecture_json", ""))
    observed_path = package_root / str(sample.get("observed_lostate", ""))
    condition_path = package_root / str(sample.get("architecture_condition", ""))
    failures: list[str] = []
    warnings: list[str] = []

    arch = load_json(arch_path) if arch_path.exists() else {}
    observed = load_json(observed_path) if observed_path.exists() else {}
    boundary = arch.get("boundary", {}).get("polygon_m", []) if isinstance(arch, dict) else []
    boundary_exists = isinstance(boundary, list) and len(boundary) >= 3
    boundary_valid = boundary_exists and polygon_area(boundary) > 1e-6
    condition_meta = arch.get("architecture_condition_metadata") or arch.get("metadata", {}).get("architecture_condition_metadata", {})
    derived = arch.get("metadata", {}).get("derived_wall_segments", [])
    raw_wall_count = int(condition_meta.get("raw_wall_anchor_count", 0) or 0)
    derived_count = int(condition_meta.get("derived_wall_segment_count", len(derived)) or 0)
    against_source = condition_meta.get("against_wall_reference_source") or (
        "explicit_wall" if raw_wall_count else "boundary_derived" if derived_count else "missing"
    )
    condition_exists = condition_path.exists() and is_png(condition_path)
    has_floor_mask = bool(condition_meta.get("architecture_condition_has_floor_or_room_mask", boundary_exists))
    has_contour = bool(condition_meta.get("architecture_condition_has_boundary_contour", derived_count > 0))

    door_window_entities = 0
    wall_entities = 0
    for entity in observed.get("furniture_instances", []) if isinstance(observed, dict) else []:
        if not isinstance(entity, dict):
            continue
        labels = {
            str(entity.get("category") or "").lower(),
            str(entity.get("reference_category") or "").lower(),
            str(entity.get("loreflection_category") or "").lower(),
            str(entity.get("raw_category") or "").lower(),
        }
        if labels & {"door", "window"}:
            door_window_entities += 1
        if "wall" in labels:
            wall_entities += 1

    if not boundary_exists:
        failures.append("boundary_polygon_exists=false")
    if not boundary_valid:
        failures.append("boundary_polygon_valid=false")
    if not condition_exists:
        failures.append("architecture_condition_image_exists=false")
    if not has_contour:
        failures.append("architecture_condition_has_boundary_contour=false")
    if against_source == "missing":
        failures.append("against_wall_reference_source=missing")
    if door_window_entities > 0:
        failures.append(f"door_window_entities_in_observed_lostate={door_window_entities}")
    if wall_entities > 0:
        failures.append(f"wall_entities_in_observed_lostate={wall_entities}")
    if raw_wall_count == 0 and derived_count > 0:
        warnings.append("raw_wall_anchor_count=0 but derived_wall_segment_count>0; acceptable R5 fallback.")

    return {
        "scene_id": scene_id,
        "boundary_polygon_exists": boundary_exists,
        "boundary_polygon_valid": boundary_valid,
        "floor_or_room_mask_exists": has_floor_mask,
        "architecture_condition_image_exists": condition_exists,
        "architecture_condition_has_boundary_contour": has_contour,
        "raw_wall_anchor_count": raw_wall_count,
        "derived_wall_segment_count": derived_count,
        "against_wall_reference_source": against_source,
        "door_anchor_count": int(condition_meta.get("door_anchor_count", 0) or 0),
        "window_anchor_count": int(condition_meta.get("window_anchor_count", 0) or 0),
        "door_window_entities_in_observed_lostate": door_window_entities,
        "wall_entities_in_observed_lostate": wall_entities,
        "failures": failures,
        "warnings": warnings,
    }


def validate_package(package_root: Path) -> dict[str, Any]:
    manifest = load_json(package_root / "manifest.json")
    samples = manifest.get("samples", []) if isinstance(manifest, dict) else []
    scene_reports = [inspect_scene(package_root, sample) for sample in samples if isinstance(sample, dict)]
    failures = [f"{r['scene_id']}: {failure}" for r in scene_reports for failure in r["failures"]]
    warnings = [f"{r['scene_id']}: {warning}" for r in scene_reports for warning in r["warnings"]]
    source_counts: dict[str, int] = {}
    for report in scene_reports:
        source = str(report["against_wall_reference_source"])
        source_counts[source] = source_counts.get(source, 0) + 1

    def count_true(key: str) -> int:
        return sum(1 for report in scene_reports if report.get(key) is True)

    return {
        "schema_version": "architecture-condition-validation-v1",
        "package_root": package_root.as_posix(),
        "scene_count": len(scene_reports),
        "boundary_polygon_exists_count": count_true("boundary_polygon_exists"),
        "boundary_polygon_valid_count": count_true("boundary_polygon_valid"),
        "floor_or_room_mask_exists_count": count_true("floor_or_room_mask_exists"),
        "architecture_condition_image_exists_count": count_true("architecture_condition_image_exists"),
        "architecture_condition_has_boundary_contour_count": count_true("architecture_condition_has_boundary_contour"),
        "raw_wall_anchor_count_total": sum(int(r["raw_wall_anchor_count"]) for r in scene_reports),
        "derived_wall_segment_count_total": sum(int(r["derived_wall_segment_count"]) for r in scene_reports),
        "against_wall_reference_source_summary": source_counts,
        "door_anchor_count_total": sum(int(r["door_anchor_count"]) for r in scene_reports),
        "window_anchor_count_total": sum(int(r["window_anchor_count"]) for r in scene_reports),
        "door_window_entities_in_observed_lostate_total": sum(int(r["door_window_entities_in_observed_lostate"]) for r in scene_reports),
        "wall_entities_in_observed_lostate_total": sum(int(r["wall_entities_in_observed_lostate"]) for r in scene_reports),
        "scene_reports": scene_reports,
        "warnings": warnings,
        "failures": failures,
        "status": "failed" if failures else "passed_with_warnings" if warnings else "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    report = validate_package(args.prototype_root)
    write_json(args.output, report)
    if report["failures"]:
        print(f"Architecture condition validation failed with {len(report['failures'])} issue(s).")
        for failure in report["failures"]:
            print(f"- {failure}")
        return 1 if args.strict else 0
    print("Architecture condition validation passed.")
    if report["warnings"]:
        print(f"Warnings are present: {len(report['warnings'])}; see {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
