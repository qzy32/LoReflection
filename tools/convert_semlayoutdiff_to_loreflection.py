#!/usr/bin/env python
"""Convert SemLayoutDiff-like samples into LoReflection local artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_pipeline.render_arch_condition import render as render_arch_condition
from tools.build_arch_json_from_semlayoutdiff import convert_toy_room_meta, parse_image_size
from tools.build_semantic_layout_from_semlayoutdiff import convert_semantic_layout


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_toy_samples(input_root: Path) -> list[Path]:
    """Find toy sample directories with both room_meta.json and semantic_objects.json."""
    if (input_root / "room_meta.json").exists() and (input_root / "semantic_objects.json").exists():
        return [input_root]
    return sorted(
        path
        for path in input_root.iterdir()
        if path.is_dir() and (path / "room_meta.json").exists() and (path / "semantic_objects.json").exists()
    )


def validate_output(output_root: Path) -> None:
    subprocess.run(
        [sys.executable, "tools/validate_all.py", "--data-root", str(output_root), "--strict"],
        cwd=REPO_ROOT,
        check=True,
    )


def convert_toy(input_root: Path, output_root: Path, palette: Path) -> dict:
    arch_dir = output_root / "arch_json_v1"
    condition_dir = output_root / "arch_condition_v1"
    semantic_dir = output_root / "gt_semantic_layout_v1"
    report_dir = output_root / "reports"
    for path in [arch_dir, condition_dir, semantic_dir, report_dir]:
        path.mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": "semlayoutdiff-conversion-report-v1",
        "input_root": str(input_root),
        "output_root": str(output_root),
        "mode": "toy",
        "total_samples": 0,
        "converted_architecture": 0,
        "converted_semantic_layout": 0,
        "failed_samples": [],
        "warnings": [],
    }

    samples = find_toy_samples(input_root)
    report["total_samples"] = len(samples)
    if not samples:
        report["warnings"].append("No toy samples found. Expected room_meta.json and semantic_objects.json.")

    for sample_dir in samples:
        sample_id = sample_dir.name
        try:
            room_meta = load_json(sample_dir / "room_meta.json")
            semantic_objects = sample_dir / "semantic_objects.json"
            image_size = parse_image_size("1024")
            arch = convert_toy_room_meta(
                room_meta,
                architecture_id=room_meta.get("architecture_id", sample_id),
                room_type=room_meta.get("room_type"),
                image_size_px=image_size,
            )
            arch_path = arch_dir / f"{sample_id}.architecture_v1.json"
            arch_path.write_text(json.dumps(arch, ensure_ascii=False, indent=2), encoding="utf-8")
            report["converted_architecture"] += 1

            condition_path = condition_dir / f"{sample_id}.arch_condition.png"
            render_arch_condition(arch, condition_path, width=image_size[0], height=image_size[1])

            semantic_path = semantic_dir / f"{sample_id}.semantic_layout.png"
            semantic_result = convert_semantic_layout(semantic_objects, palette, semantic_path, "toy_json")
            report["converted_semantic_layout"] += 1 if semantic_result.get("converted") else 0
            report["warnings"].extend(f"{sample_id}: {warning}" for warning in semantic_result.get("warnings", []))
        except Exception as exc:  # Keep batch conversion non-fatal across samples.
            report["failed_samples"].append({"sample_id": sample_id, "error": str(exc)})

    report_path = report_dir / "semlayoutdiff_conversion_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", required=True, type=Path, help="SemLayoutDiff-like input root.")
    parser.add_argument("--output-root", required=True, type=Path, help="Output root for LoReflection artifacts.")
    parser.add_argument("--palette", type=Path, default=Path("configs/palette_v1.json"), help="LoReflection palette JSON.")
    parser.add_argument("--mode", required=True, choices=["toy"], help="Conversion mode. Only toy is implemented locally.")
    args = parser.parse_args()

    # TODO(server): add modes for real SemLayoutDiff preprocessed outputs after
    # inspecting the upstream npy/pickle/json conventions on the server.
    report = convert_toy(args.input_root, args.output_root, args.palette)
    validate_output(args.output_root)
    report_path = args.output_root / "reports" / "semlayoutdiff_conversion_report.json"
    print(f"Wrote SemLayoutDiff conversion report to {report_path}")
    if report["failed_samples"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

