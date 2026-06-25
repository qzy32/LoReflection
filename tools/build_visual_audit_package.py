#!/usr/bin/env python
"""Build a lightweight visual audit package for a LoReflection prototype."""

from __future__ import annotations

import argparse
import csv
import html
import json
import shutil
from pathlib import Path
from typing import Any

from render_topdown_audit_v2 import build_visual_audit_v2


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def copy_if_exists(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dst)
    return dst.as_posix()


def count_categories(observed: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entity in observed.get("furniture_instances", []):
        if not isinstance(entity, dict):
            continue
        cat = str(entity.get("category") or entity.get("loreflection_category") or "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def build_package(prototype_root: Path, output_dir: Path, strict: bool) -> dict[str, Any]:
    manifest = load_json(prototype_root / "manifest.json")
    conversion = load_json(prototype_root / "reports" / "conversion_report.json")
    arch_validation_path = prototype_root / "reports" / "architecture_condition_validation.json"
    arch_validation = load_json(arch_validation_path) if arch_validation_path.exists() else {}
    scene_validation = {item["scene_id"]: item for item in arch_validation.get("scene_reports", []) if isinstance(item, dict)}
    output_dir.mkdir(parents=True, exist_ok=True)
    per_scene_dir = output_dir / "per_scene"
    per_scene_dir.mkdir(exist_ok=True)

    contact_src = prototype_root / "preview" / "contact_sheet.png"
    contact_dst = output_dir / "contact_sheet_annotated.png"
    copy_if_exists(contact_src, contact_dst)

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for sample in manifest.get("samples", []):
        if not isinstance(sample, dict):
            continue
        scene_id = str(sample.get("scene_id", "unknown"))
        observed_path = prototype_root / str(sample.get("observed_lostate", ""))
        arch_path = prototype_root / str(sample.get("architecture_json", ""))
        observed = load_json(observed_path) if observed_path.exists() else {}
        arch = load_json(arch_path) if arch_path.exists() else {}
        condition_meta = arch.get("architecture_condition_metadata") or arch.get("metadata", {}).get("architecture_condition_metadata", {})
        category_hist = count_categories(observed)
        preview_rel = sample.get("preview", "")
        arch_condition_rel = sample.get("architecture_condition", "")
        semantic_rel = sample.get("semantic_layout", "")
        preview_copy = f"per_scene/{scene_id}_preview.png"
        copy_if_exists(prototype_root / str(preview_rel), output_dir / preview_copy)
        row = {
            "scene_id": scene_id,
            "room_type": sample.get("room_type", arch.get("room_type", "unknown")),
            "num_entities": sum(category_hist.values()),
            "category_histogram": category_hist,
            "sofa_count": category_hist.get("sofa", 0),
            "table_count": category_hist.get("table", 0),
            "lamp_count": sum(category_hist.get(k, 0) for k in ["lamp", "pendant_lamp", "ceiling_lamp", "floor_lamp"]),
            "door_anchor_count": condition_meta.get("door_anchor_count", 0),
            "window_anchor_count": condition_meta.get("window_anchor_count", 0),
            "raw_wall_anchor_count": condition_meta.get("raw_wall_anchor_count", 0),
            "derived_wall_segment_count": condition_meta.get("derived_wall_segment_count", 0),
            "against_wall_reference_source": condition_meta.get("against_wall_reference_source", "missing"),
            "architecture_condition_has_floor_or_room_mask": condition_meta.get("architecture_condition_has_floor_or_room_mask", False),
            "architecture_condition_has_boundary_contour": condition_meta.get("architecture_condition_has_boundary_contour", False),
            "floor_mesh_source": condition_meta.get("floor_mesh_source", False),
            "core_missing_transform_count": conversion.get("transform_extraction", {}).get("core_missing_transform_count", 0),
            "lamp_missing_transform_count": conversion.get("transform_extraction", {}).get("lamp_missing_transform_count", 0),
            "unknown_skipped": conversion.get("semantic_layout", {}).get("unknown_skipped", 0),
            "accessory_skipped": conversion.get("semantic_layout", {}).get("accessory_skipped", 0),
            "warnings": observed.get("warnings", []),
            "preview_path": preview_copy,
            "architecture_condition_path": arch_condition_rel,
            "semantic_layout_path": semantic_rel,
            "observed_lostate_path": sample.get("observed_lostate", ""),
            "architecture_json_path": sample.get("architecture_json", ""),
            "validation_status": scene_validation.get(scene_id, {}).get("against_wall_reference_source", ""),
        }
        if strict and row["against_wall_reference_source"] == "missing":
            failures.append(f"{scene_id}: missing against-wall reference")
        rows.append(row)

    write_json(output_dir / "scene_summary.json", {"scene_count": len(rows), "scenes": rows, "failures": failures})
    with (output_dir / "scene_summary.csv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "scene_id",
            "room_type",
            "num_entities",
            "category_histogram",
            "sofa_count",
            "table_count",
            "lamp_count",
            "door_anchor_count",
            "window_anchor_count",
            "raw_wall_anchor_count",
            "derived_wall_segment_count",
            "against_wall_reference_source",
            "architecture_condition_has_floor_or_room_mask",
            "architecture_condition_has_boundary_contour",
            "floor_mesh_source",
            "core_missing_transform_count",
            "lamp_missing_transform_count",
            "unknown_skipped",
            "accessory_skipped",
            "warnings",
            "preview_path",
            "architecture_condition_path",
            "semantic_layout_path",
            "observed_lostate_path",
            "architecture_json_path",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            csv_row["category_histogram"] = json.dumps(row["category_histogram"], ensure_ascii=False)
            csv_row["warnings"] = json.dumps(row["warnings"], ensure_ascii=False)
            writer.writerow({k: csv_row.get(k, "") for k in fieldnames})

    readme = """# LoReflection Visual Audit Package

## Checklist

### A. Architecture condition
- room/floor mask exists;
- boundary/wall contour is visible;
- door anchors are placed near boundary/openings;
- window anchors are placed near boundary;
- wall is not a furniture entity;
- if raw wall anchor is 0, boundary-derived wall segments are acceptable;
- mark `needs_wall_channel` only if boundary contour is visually weak.

### B. Furniture semantic
- furniture stays inside room;
- sofa/table/chair/desk categories are visually separated;
- lamp appears as semantic target and is not abnormally large/outside;
- door/window/wall are not shown as furniture instances.

### C. Scale-to-50 decision
- pass
- needs_arch_condition_fix
- needs_geometry_fix
- needs_category_fix
- fail
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    cards = []
    for row in rows:
        cards.append(
            f"<section><h2>{html.escape(row['scene_id'])}</h2>"
            f"<p>room={html.escape(str(row['room_type']))}, entities={row['num_entities']}, "
            f"wall_ref={html.escape(str(row['against_wall_reference_source']))}, "
            f"derived_walls={row['derived_wall_segment_count']}</p>"
            f"<img src='{html.escape(row['preview_path'])}' style='width:320px;image-rendering:pixelated'>"
            f"<pre>{html.escape(json.dumps(row['category_histogram'], ensure_ascii=False, indent=2))}</pre>"
            "</section>"
        )
    index = (
        "<!doctype html><meta charset='utf-8'><title>LoReflection Visual Audit</title>"
        "<style>body{font-family:sans-serif;max-width:1200px;margin:24px auto}"
        "section{border-bottom:1px solid #ddd;padding:16px 0}img{border:1px solid #999}</style>"
        "<h1>LoReflection Visual Audit</h1>"
        "<p>Use this package for manual inspection only. No training output is included.</p>"
        "<h2>Contact sheet</h2><img src='contact_sheet_annotated.png' style='width:520px'>"
        + "\n".join(cards)
    )
    (output_dir / "index.html").write_text(index, encoding="utf-8")
    return {
        "output_dir": output_dir.as_posix(),
        "scene_count": len(rows),
        "failures": failures,
        "files": [
            "index.html",
            "README.md",
            "scene_summary.csv",
            "scene_summary.json",
            "contact_sheet_annotated.png",
            "per_scene/",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--style-config", type=Path, default=None)
    parser.add_argument("--layout-version", choices=["v1", "v2", "semlayoutdiff_grounded_v1"], default="v1")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    if args.layout_version in {"v2", "semlayoutdiff_grounded_v1"}:
        report = build_visual_audit_v2(args.prototype_root, args.output_dir, args.style_config, args.strict, layout_tag=args.layout_version)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    report = build_package(args.prototype_root, args.output_dir, args.strict)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if args.strict and report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
