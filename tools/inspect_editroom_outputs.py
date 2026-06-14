#!/usr/bin/env python
"""Inspect an EditRoom checkout/output directory without requiring real data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_FILES = [
    "tools/generate_perturbations.py",
    "tools/editroomperturb.py",
    "tools/generate_prompt.py",
    "src/train_edit.py",
    "configs/bedroom_sg2sc_diffusion.yaml",
    "configs/bedroom_sg_diffusion.yaml",
]


def inspect_paths(editroom_root: Path, sample_dir: Path) -> dict:
    found_files: list[str] = []
    missing_expected_files: list[str] = []
    recommended_next_steps: list[str] = []

    if editroom_root.exists():
        for rel in EXPECTED_FILES:
            path = editroom_root / rel
            if path.exists():
                found_files.append(str(path))
            else:
                missing_expected_files.append(str(path))
        if missing_expected_files:
            recommended_next_steps.append("EditRoom root exists, but some expected files are missing. Verify the checkout or upstream version.")
    else:
        missing_expected_files.extend(str(editroom_root / rel) for rel in EXPECTED_FILES)
        recommended_next_steps.append("EditRoom repo was not found locally. This is OK for toy adapter tests; set EDITROOM_ROOT on the server.")

    if sample_dir.exists():
        toy_files = sorted(path for path in sample_dir.rglob("*") if path.is_file())
        found_files.extend(str(path) for path in toy_files)
        for name in ["before_layout.json", "after_layout.json", "edit_instruction.json"]:
            if not any(path.name == name for path in toy_files):
                missing_expected_files.append(str(sample_dir / "<sample>" / name))
                recommended_next_steps.append(f"Toy sample dir exists but no {name} was found.")
    else:
        missing_expected_files.append(str(sample_dir))
        recommended_next_steps.append("Sample dir was not found. Create examples/toy_editroom or point --sample-dir to converted EditRoom outputs.")

    if not recommended_next_steps:
        recommended_next_steps.append("Expected local adapter inputs are present. Run convert_editroom_to_loreflection.py in toy mode.")

    return {
        "schema_version": "editroom-inspect-report-v1",
        "editroom_root": str(editroom_root),
        "sample_dir": str(sample_dir),
        "found_files": found_files,
        "missing_expected_files": missing_expected_files,
        "recommended_next_steps": recommended_next_steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--editroom-root", required=True, type=Path, help="Path to an EditRoom checkout.")
    parser.add_argument("--sample-dir", required=True, type=Path, help="Path to toy or converted EditRoom-like samples.")
    parser.add_argument("--report", required=True, type=Path, help="Output JSON inspection report.")
    args = parser.parse_args()

    report = inspect_paths(args.editroom_root, args.sample_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote EditRoom inspection report to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

