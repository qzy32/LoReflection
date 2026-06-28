#!/usr/bin/env python3
"""Validate Qwen Architecture In-Context metadata rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = [
    "image",
    "prompt",
    "context_image",
    "sample_id",
    "goal_lostate",
    "prompt_package",
    "verifier_refs",
]
PATH_COLUMNS = ["image", "context_image", "goal_lostate", "prompt_package", "verifier_refs"]


def _resolve(path_text: str, metadata_path: Path, dataset_base: Path | None) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    if dataset_base is not None:
        candidate = dataset_base / path
        if candidate.exists():
            return candidate
    return metadata_path.parent / path


def validate_metadata(metadata_path: Path, dataset_base: Path | None = None) -> dict[str, Any]:
    failures: list[str] = []
    rows: list[dict[str, str]] = []
    with metadata_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [name for name in REQUIRED_COLUMNS if name not in fieldnames]
        unexpected = [name for name in fieldnames if name not in REQUIRED_COLUMNS]
        if missing:
            failures.append(f"missing required columns: {missing}")
        if unexpected:
            failures.append(f"unexpected metadata columns: {unexpected}")
        for row in reader:
            rows.append(row)

    for idx, row in enumerate(rows, 1):
        for col in REQUIRED_COLUMNS:
            if not str(row.get(col, "")).strip():
                failures.append(f"row {idx}: empty required column {col}")
        for col in PATH_COLUMNS:
            value = str(row.get(col, "")).strip()
            if value and not _resolve(value, metadata_path, dataset_base).exists():
                failures.append(f"row {idx}: path does not exist for {col}: {value}")

    return {
        "metadata_path": str(metadata_path),
        "dataset_base": str(dataset_base) if dataset_base else None,
        "row_count": len(rows),
        "required_columns": REQUIRED_COLUMNS,
        "allowed_columns": REQUIRED_COLUMNS,
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", nargs="?", type=Path, help="metadata.csv to validate")
    parser.add_argument("--dataset-base", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None, help="optional JSON audit output")
    args = parser.parse_args()
    if args.metadata is None:
        parser.print_help()
        return 0

    report = validate_metadata(args.metadata, args.dataset_base)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
