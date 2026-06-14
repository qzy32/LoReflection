#!/usr/bin/env python
"""Inspect a SemLayoutDiff checkout/output directory without requiring real data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_FILES = [
    "preprocess/scripts/data_processor.py",
    "preprocess/scripts/data_to_npy.py",
    "preprocess/scripts/pickle_threed_front_dataset.py",
    "preprocess/scripts/json_threed_future_dataset.py",
    "render_dataset_improved_mat.py",
    "scripts/train_sldn.py",
    "scripts/sample_layout.py",
]


def inspect_paths(semlayoutdiff_root: Path, sample_dir: Path) -> dict:
    """Return a non-fatal report for expected SemLayoutDiff and toy sample paths."""
    found_files: list[str] = []
    missing_expected_files: list[str] = []
    recommended_next_steps: list[str] = []

    if semlayoutdiff_root.exists():
        for rel in EXPECTED_FILES:
            path = semlayoutdiff_root / rel
            if path.exists():
                found_files.append(str(path))
            else:
                missing_expected_files.append(str(path))
        if missing_expected_files:
            recommended_next_steps.append("SemLayoutDiff root exists, but some expected scripts are missing. Verify the checkout path or upstream version.")
    else:
        missing_expected_files.extend(str(semlayoutdiff_root / rel) for rel in EXPECTED_FILES)
        recommended_next_steps.append("SemLayoutDiff repo was not found locally. This is OK for toy adapter tests; set SEMLAYOUTDIFF_ROOT on the server.")

    if sample_dir.exists():
        toy_files = sorted(path for path in sample_dir.rglob("*") if path.is_file())
        found_files.extend(str(path) for path in toy_files)
        if not any(path.name == "room_meta.json" for path in toy_files):
            missing_expected_files.append(str(sample_dir / "<sample>/room_meta.json"))
            recommended_next_steps.append("Toy sample dir exists but no room_meta.json was found.")
        if not any(path.name == "semantic_objects.json" for path in toy_files):
            missing_expected_files.append(str(sample_dir / "<sample>/semantic_objects.json"))
            recommended_next_steps.append("Toy sample dir exists but no semantic_objects.json was found.")
    else:
        missing_expected_files.append(str(sample_dir))
        recommended_next_steps.append("Sample dir was not found. Create examples/toy_semlayoutdiff or point --sample-dir to converted server outputs.")

    if not recommended_next_steps:
        recommended_next_steps.append("Expected local adapter inputs are present. Run convert_semlayoutdiff_to_loreflection.py in toy mode.")

    return {
        "schema_version": "semlayoutdiff-inspect-report-v1",
        "semlayoutdiff_root": str(semlayoutdiff_root),
        "sample_dir": str(sample_dir),
        "found_files": found_files,
        "missing_expected_files": missing_expected_files,
        "recommended_next_steps": recommended_next_steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", required=True, type=Path, help="Path to a SemLayoutDiff checkout.")
    parser.add_argument("--sample-dir", required=True, type=Path, help="Path to toy or converted SemLayoutDiff-like samples.")
    parser.add_argument("--report", required=True, type=Path, help="Output JSON inspection report.")
    args = parser.parse_args()

    report = inspect_paths(args.semlayoutdiff_root, args.sample_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote SemLayoutDiff inspection report to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

