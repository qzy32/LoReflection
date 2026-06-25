#!/usr/bin/env python3
"""Validate SemLayoutDiff-grounded LoReflection visual audit outputs."""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from typing import Any


ARCH_REQUIRED = {
    "Room interior / Floor",
    "Boundary",
    "Derived wall",
    "Door",
    "Window",
    "Clearance",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def validate_links(html_path: Path, root: Path) -> list[str]:
    if not html_path.exists():
        return ["index.html"]
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    broken = []
    for link in re.findall(r"""(?:href|src)=['"]([^'"]+)['"]""", text):
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if not (root / link).exists():
            broken.append(link)
    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--visual-audit-dir", type=Path, required=True)
    parser.add_argument("--palette", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    palette = dict(load_json(args.palette).get("colors", {}))
    summary = load_json(args.visual_audit_dir / "scene_summary.json")
    failures: list[str] = []
    counts = {
        "boundary_visible": 0,
        "door_visible": 0,
        "window_visible": 0,
        "furniture_legend_complete": 0,
        "palette_mismatches": 0,
        "transform_mismatches": 0,
        "crop_aspect_problems": 0,
    }
    scene_reports = []
    for scene in summary.get("scenes", []):
        scene_id = scene.get("scene_id")
        image_rel = scene.get("image")
        if not image_rel:
            failures.append(f"{scene_id}: missing image path in scene summary")
            continue
        image_path = args.visual_audit_dir / image_rel
        sidecar_path = args.visual_audit_dir / image_rel.replace(".png", ".json")
        if not image_path.exists():
            failures.append(f"{scene_id}: missing audit png")
            continue
        if not sidecar_path.exists():
            failures.append(f"{scene_id}: missing audit sidecar")
            continue
        w, h = png_size(image_path)
        sidecar = load_json(sidecar_path)
        present = set(sidecar.get("present_categories", []))
        legend = set(sidecar.get("furniture_legend_categories", []))
        missing_categories = sorted(present - legend)
        color_mismatches = [
            cat
            for cat, color in sidecar.get("furniture_legend_colors", {}).items()
            if cat in palette and str(palette[cat]).lower() != str(color).lower()
        ]
        boundary = bool(sidecar.get("boundary_rendered"))
        door_ok = int(sidecar.get("doors_rendered", 0)) >= int(sidecar.get("doors_present", 0))
        window_ok = int(sidecar.get("windows_rendered", 0)) >= int(sidecar.get("windows_present", 0))
        transform_ok = bool(sidecar.get("same_transform_across_panels"))
        aspect_ok = bool(sidecar.get("equal_aspect_ratio")) and w >= 1800 and h >= 850
        arch_ok = set(sidecar.get("architecture_legend_items", [])) >= ARCH_REQUIRED
        no_arch_as_furniture = not any(cat in {"door", "window", "wall"} for cat in present)
        checks = {
            "boundary_visible": boundary,
            "door_visible_if_present": door_ok,
            "window_visible_if_present": window_ok,
            "furniture_legend_complete": not missing_categories,
            "legend_color_matches_palette": not color_mismatches,
            "same_transform_across_panels": transform_ok,
            "equal_aspect_ratio_and_min_size": aspect_ok,
            "architecture_legend_complete": arch_ok,
            "no_door_window_wall_as_furniture": no_arch_as_furniture,
        }
        if boundary:
            counts["boundary_visible"] += 1
        if door_ok:
            counts["door_visible"] += 1
        if window_ok:
            counts["window_visible"] += 1
        if not missing_categories:
            counts["furniture_legend_complete"] += 1
        counts["palette_mismatches"] += len(color_mismatches)
        if not transform_ok:
            counts["transform_mismatches"] += 1
        if not aspect_ok:
            counts["crop_aspect_problems"] += 1
        for key, ok in checks.items():
            if not ok:
                failures.append(f"{scene_id}: {key} failed")
        scene_reports.append(
            {
                "scene_id": scene_id,
                "image_size": [w, h],
                "missing_legend_categories": missing_categories,
                "palette_mismatches": color_mismatches,
                **checks,
            }
        )

    broken_links = validate_links(args.visual_audit_dir / "index.html", args.visual_audit_dir)
    for link in broken_links:
        failures.append(f"broken index link: {link}")
    equivalence_path = args.visual_audit_dir / "reports" / "canonical_output_equivalence.json"
    equivalence = load_json(equivalence_path) if equivalence_path.exists() else {"result": False, "missing": True}
    if not equivalence.get("result"):
        failures.append("canonical equivalence failed")
    if not (args.visual_audit_dir / "reports" / "final_draw_order.json").exists():
        failures.append("final_draw_order.json missing")

    report = {
        "report_version": "semlayoutdiff_grounded_visualization_validation_v1",
        "scene_count": len(summary.get("scenes", [])),
        "counts": counts,
        "broken_index_links": broken_links,
        "canonical_equivalence": equivalence,
        "scene_reports": scene_reports,
        "failures": failures,
        "result": "passed" if not failures else "failed",
    }
    write_json(args.output, report)
    if failures:
        print(json.dumps({"result": "failed", "failures": failures}, indent=2, ensure_ascii=False))
        return 1 if args.strict else 0
    print("SemLayoutDiff-grounded visualization validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
