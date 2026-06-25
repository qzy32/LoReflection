#!/usr/bin/env python3
"""Validate human-facing visual audit V2 readability outputs."""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from typing import Any


ARCH_LEGEND_REQUIRED = {
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_palette(path: Path) -> dict[str, str]:
    payload = load_json(path)
    return dict(payload.get("colors", {}))


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def validate_links(html_path: Path, root: Path) -> list[str]:
    if not html_path.exists():
        return ["index.html missing"]
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    links = re.findall(r"""(?:href|src)=['"]([^'"]+)['"]""", text)
    broken = []
    for link in links:
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (root / link).resolve()
        try:
            target.relative_to(root.parent.parent.parent.parent if root.parts else root)
        except ValueError:
            pass
        if not target.exists():
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

    palette = load_palette(args.palette)
    scene_summary_path = args.visual_audit_dir / "scene_summary.json"
    summary = load_json(scene_summary_path)
    scene_reports = []
    failures: list[str] = []
    counts = {
        "boundary_visible": 0,
        "derived_wall_visible": 0,
        "doors_rendered": 0,
        "windows_rendered": 0,
        "complete_architecture_legend": 0,
        "complete_furniture_legend": 0,
        "palette_color_mismatches": 0,
        "panel_transform_mismatches": 0,
    }
    for scene in summary.get("scenes", []):
        scene_id = scene.get("scene_id")
        sidecar_path = args.visual_audit_dir / "per_scene" / f"{scene_id}_audit_v2.json"
        if not sidecar_path.exists():
            failures.append(f"{scene_id}: missing audit sidecar")
            continue
        sidecar = load_json(sidecar_path)
        image_path = args.visual_audit_dir / sidecar["image"]
        image_exists = image_path.exists()
        width = height = 0
        if image_exists:
            width, height = png_size(image_path)
        else:
            failures.append(f"{scene_id}: missing audit image")

        missing_categories = sorted(set(sidecar.get("present_categories", [])) - set(sidecar.get("furniture_legend_categories", [])))
        color_mismatches = []
        for category, color in sidecar.get("furniture_legend_colors", {}).items():
            if palette.get(category) and palette[category].lower() != str(color).lower():
                color_mismatches.append(category)

        arch_complete = set(sidecar.get("architecture_legend_items", ARCH_LEGEND_REQUIRED)) >= ARCH_LEGEND_REQUIRED
        furniture_complete = not missing_categories
        same_transform = bool(sidecar.get("same_transform_across_panels"))
        equal_aspect = bool(sidecar.get("equal_aspect_ratio"))
        boundary = bool(sidecar.get("boundary_rendered"))
        derived_wall = bool(sidecar.get("derived_wall_rendered"))
        doors_ok = int(sidecar.get("doors_rendered", 0)) >= int(sidecar.get("doors_present", 0))
        windows_ok = int(sidecar.get("windows_rendered", 0)) >= int(sidecar.get("windows_present", 0))

        if boundary:
            counts["boundary_visible"] += 1
        if derived_wall:
            counts["derived_wall_visible"] += 1
        if doors_ok:
            counts["doors_rendered"] += 1
        if windows_ok:
            counts["windows_rendered"] += 1
        if arch_complete:
            counts["complete_architecture_legend"] += 1
        if furniture_complete:
            counts["complete_furniture_legend"] += 1
        if color_mismatches:
            counts["palette_color_mismatches"] += len(color_mismatches)
        if not same_transform:
            counts["panel_transform_mismatches"] += 1

        hard_checks = {
            "image_exists": image_exists,
            "minimum_image_width": width >= 1800,
            "minimum_image_height": height >= 850,
            "architecture_legend_complete": arch_complete,
            "furniture_legend_matches_present_categories": furniture_complete,
            "boundary_rendered": boundary,
            "derived_wall_rendered": derived_wall,
            "door_rendered_if_present": doors_ok,
            "window_rendered_if_present": windows_ok,
            "same_transform_across_panels": same_transform,
            "equal_aspect_ratio": equal_aspect,
            "legend_color_matches_palette": not color_mismatches,
        }
        for key, ok in hard_checks.items():
            if not ok:
                failures.append(f"{scene_id}: {key} failed")
        scene_reports.append(
            {
                "scene_id": scene_id,
                "image_width": width,
                "image_height": height,
                "missing_legend_categories": missing_categories,
                "palette_color_mismatches": color_mismatches,
                **hard_checks,
            }
        )

    contact_sheet_exists = (args.visual_audit_dir / "contact_sheet_v2.png").exists()
    palette_legend_exists = (args.visual_audit_dir / "palette_legend.png").exists()
    index_broken_links = validate_links(args.visual_audit_dir / "index.html", args.visual_audit_dir)
    if not contact_sheet_exists:
        failures.append("contact_sheet_v2.png missing")
    if not palette_legend_exists:
        failures.append("palette_legend.png missing")
    for link in index_broken_links:
        failures.append(f"broken index link: {link}")

    equivalence_path = args.visual_audit_dir / "reports" / "canonical_output_equivalence.json"
    equivalence = load_json(equivalence_path) if equivalence_path.exists() else {"result": False, "missing": True}
    if not equivalence.get("result"):
        failures.append("canonical output equivalence failed")

    report = {
        "report_version": "visual_audit_readability_v1",
        "prototype_root": str(args.prototype_root),
        "visual_audit_dir": str(args.visual_audit_dir),
        "scene_count": len(summary.get("scenes", [])),
        "counts": counts,
        "contact_sheet_exists": contact_sheet_exists,
        "palette_legend_exists": palette_legend_exists,
        "index_relative_links_valid": not index_broken_links,
        "broken_index_links": index_broken_links,
        "canonical_output_equivalence": equivalence,
        "scene_reports": scene_reports,
        "failures": failures,
        "result": "passed" if not failures else "failed",
    }
    write_json(args.output, report)
    if failures:
        print(json.dumps({"result": "failed", "failures": failures}, indent=2, ensure_ascii=False))
        return 1 if args.strict else 0
    print("Visual audit readability validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
