#!/usr/bin/env python3
"""Audit Architecture In-Context dataset scale and inverse-transform readiness."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _bbox(points: list[list[float]]) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _area_from_bbox(box: tuple[float, float, float, float] | None) -> float | None:
    if box is None:
        return None
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _estimate_scale(poly_m: list[list[float]], poly_px: list[list[float]]) -> float | None:
    bm = _bbox(poly_m)
    bp = _bbox(poly_px)
    if bm is None or bp is None:
        return None
    wm = max(1e-9, bm[2] - bm[0])
    hm = max(1e-9, bm[3] - bm[1])
    wp = max(1e-9, bp[2] - bp[0])
    hp = max(1e-9, bp[3] - bp[1])
    return float((wp / wm + hp / hm) / 2.0)


def audit_dataset(dataset_root: Path, output: Path | None = None) -> dict[str, Any]:
    metadata = dataset_root / "metadata.csv"
    rows = list(csv.DictReader(metadata.open("r", encoding="utf-8", newline="")))
    counts = {
        "source_scene_json": 0,
        "polygon_m": 0,
        "polygon_px": 0,
        "layout_metric_fields": 0,
        "metric_transform": 0,
        "implicit_transform": 0,
    }
    boundary_sources: dict[str, int] = {}
    room_type_unknown = 0
    scales: list[float] = []
    room_areas_m: list[float] = []
    floor_areas_px: list[float] = []
    samples: list[dict[str, Any]] = []
    for row in rows:
        sid = row["sample_id"]
        arch_path = dataset_root / "meta" / f"{sid}_architecture.json"
        layout_path = dataset_root / "meta" / f"{sid}_layout.json"
        manifest_path = dataset_root / "meta" / f"{sid}_sample_manifest.json"
        arch = _read_json(arch_path)
        layout = _read_json(layout_path)
        manifest = _read_json(manifest_path)
        source = layout.get("source", {}) if isinstance(layout.get("source"), dict) else {}
        if source.get("source_scene_json"):
            counts["source_scene_json"] += 1
        boundary = arch.get("boundary", {}) if isinstance(arch.get("boundary"), dict) else {}
        poly_m = boundary.get("polygon_m") or []
        poly_px = boundary.get("polygon_px") or []
        if poly_m:
            counts["polygon_m"] += 1
        if poly_px:
            counts["polygon_px"] += 1
        scale = _estimate_scale(poly_m, poly_px) if poly_m and poly_px else None
        if scale is not None:
            scales.append(scale)
            counts["implicit_transform"] += 1
        area_m = _area_from_bbox(_bbox(poly_m)) if poly_m else None
        area_px = _area_from_bbox(_bbox(poly_px)) if poly_px else None
        if area_m is not None:
            room_areas_m.append(area_m)
        if area_px is not None:
            floor_areas_px.append(area_px)
        objects = layout.get("objects", []) if isinstance(layout.get("objects"), list) else []
        metric_ok = all(
            isinstance(obj, dict)
            and "center_m" in obj
            and "size_m" in obj
            and "orientation_deg" in obj
            for obj in objects
        ) and bool(objects)
        if metric_ok:
            counts["layout_metric_fields"] += 1
        if manifest.get("metric_transform") or manifest.get("render_transform") or arch.get("metric_transform"):
            counts["metric_transform"] += 1
        bsrc = str(boundary.get("boundary_source") or manifest.get("boundary_source") or source.get("boundary_source") or "unknown")
        boundary_sources[bsrc] = boundary_sources.get(bsrc, 0) + 1
        room_type = str(layout.get("room_type") or manifest.get("room_type") or "unknown").lower()
        if room_type in {"", "unknown", "none"}:
            room_type_unknown += 1
        samples.append(
            {
                "sample_id": sid,
                "source_scene_json_exists": bool(source.get("source_scene_json")),
                "has_polygon_m": bool(poly_m),
                "has_polygon_px": bool(poly_px),
                "has_layout_metric_fields": metric_ok,
                "has_explicit_metric_transform": bool(manifest.get("metric_transform") or manifest.get("render_transform") or arch.get("metric_transform")),
                "estimated_px_per_meter": scale,
                "room_bbox_area_m": area_m,
                "floor_bbox_area_px": area_px,
                "room_type": room_type,
                "boundary_source": bsrc,
            }
        )
    n = max(1, len(rows))
    # In normalized_v1, pixel bbox areas cluster tightly while metric areas vary.
    px_var = (max(floor_areas_px) - min(floor_areas_px)) / max(1.0, max(floor_areas_px)) if floor_areas_px else None
    m_var = (max(room_areas_m) - min(room_areas_m)) / max(1.0, max(room_areas_m)) if room_areas_m else None
    normalized_risk = True if counts["metric_transform"] == 0 else False
    report = {
        "dataset_root": str(dataset_root),
        "num_samples": len(rows),
        "architecture_source_of_truth": "raw_3dfront_json",
        "qwen_generates_architecture": False,
        "qwen_generates_furniture_only": True,
        "requires_inverse_transform_for_furniture": True,
        "source_scene_json_exists_rate": counts["source_scene_json"] / n,
        "polygon_m_exists_rate": counts["polygon_m"] / n,
        "polygon_px_exists_rate": counts["polygon_px"] / n,
        "layout_metric_fields_rate": counts["layout_metric_fields"] / n,
        "metric_transform_exists_rate": counts["metric_transform"] / n,
        "implicit_transform_recoverable_rate": counts["implicit_transform"] / n,
        "implicit_transform_recoverable": counts["implicit_transform"] == len(rows),
        "estimated_px_per_meter_min": min(scales) if scales else None,
        "estimated_px_per_meter_max": max(scales) if scales else None,
        "room_bbox_area_m_variation": m_var,
        "floor_bbox_area_px_variation": px_var,
        "boundary_source_distribution": boundary_sources,
        "bbox_boundary_fallback_rate": boundary_sources.get("bbox", 0) / n + boundary_sources.get("room_bbox", 0) / n,
        "room_type_unknown_rate": room_type_unknown / n,
        "normalized_v1_scale_risk": normalized_risk,
        "metric_v2_recommended": True,
        "recommendation": "add explicit metric_transform before P1-1000" if normalized_risk else "explicit metric transform present; verify inverse parser numerically",
        "samples": samples[:20],
    }
    output = output or dataset_root / "audits" / "architecture_condition_scale_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = audit_dataset(args.dataset_root, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
