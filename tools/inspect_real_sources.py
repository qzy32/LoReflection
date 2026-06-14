#!/usr/bin/env python
"""Inspect configured server source paths without running conversion or training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SOURCE_KEYS = [
    "LOREFLECTION_ROOT",
    "SEMLAYOUTDIFF_ROOT",
    "EDITROOM_ROOT",
    "DIFFSYNTH_ROOT",
    "QWEN_VL_REPO",
    "THREED_FRONT_ROOT",
    "THREED_FUTURE_ROOT",
    "QWEN25_VL_MODEL_PATH",
    "QWEN_IMAGE_MODEL_PATH",
    "DIFFSYNTH_INPAINT_MODEL_PATH",
    "INSTANTX_INPAINT_MODEL_PATH",
    "OUTPUT_ROOT",
]

EXPECTED_HINTS = {
    "SEMLAYOUTDIFF_ROOT": [
        "preprocess/scripts/data_processor.py",
        "preprocess/scripts/data_to_npy.py",
        "scripts/sample_layout.py",
    ],
    "EDITROOM_ROOT": [
        "tools/generate_perturbations.py",
        "tools/editroomperturb.py",
        "src/train_edit.py",
    ],
    "DIFFSYNTH_ROOT": ["README.md"],
    "QWEN_VL_REPO": ["README.md"],
    "LOREFLECTION_ROOT": ["README.md", "tools/check_server_paths.py"],
}


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def is_placeholder(value: str) -> bool:
    return not value or value.startswith("/server/path/to/")


def sample_files(root: Path, max_files: int) -> list[str]:
    if not root.exists() or not root.is_dir():
        return []
    files = []
    for path in root.rglob("*"):
        if path.is_file():
            try:
                files.append(path.relative_to(root).as_posix())
            except ValueError:
                files.append(path.as_posix())
        if len(files) >= max_files:
            break
    return files


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def inspect_sources(env_file: Path, max_files: int) -> dict:
    values = read_env(env_file)
    checks = {}
    warnings = []
    for key in SOURCE_KEYS:
        value = values.get(key, "")
        placeholder = is_placeholder(value)
        configured = bool(value)
        path = Path(value) if configured else None
        exists = bool(path and path.exists() and not placeholder)
        hint_results = []
        if exists:
            for hint in EXPECTED_HINTS.get(key, []):
                hint_path = path / hint
                hint_results.append({"path": hint, "exists": hint_path.exists()})
                if not hint_path.exists():
                    warnings.append(f"{key} missing expected hint file: {hint}")
        elif not configured:
            warnings.append(f"{key} is not configured.")
        elif placeholder:
            warnings.append(f"{key} is still a placeholder.")
        else:
            warnings.append(f"{key} path does not exist: {value}")
        checks[key] = {
            "value": value,
            "configured": configured,
            "exists": exists,
            "is_placeholder": placeholder,
            "expected_hints": hint_results,
            "sample_files": sample_files(path, max_files) if exists and path else [],
        }
    return {
        "schema_version": "real-source-inspection-report-v1",
        "env_file": env_file.as_posix(),
        "max_files": max_files,
        "checks": checks,
        "warnings": warnings,
        "dry_run": True,
        "message": "Real source inspection dry-run only. No conversion, training, model loading, or data loading was executed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True, help=".env-style path file.")
    parser.add_argument("--output", type=Path, required=True, help="JSON inspection report path.")
    parser.add_argument("--max-files", type=int, default=5, help="Maximum sample files to list per existing directory.")
    parser.add_argument("--verbose", action="store_true", help="Print warnings and found source summaries.")
    args = parser.parse_args()

    report = inspect_sources(args.env_file, args.max_files)
    write_json(args.output, report)
    print(f"Wrote real source inspection report to {args.output}")
    print("Real source inspection dry-run only. No conversion, training, model loading, or data loading was executed.")
    if args.verbose and report["warnings"]:
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
