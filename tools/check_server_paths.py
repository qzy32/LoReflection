#!/usr/bin/env python
"""Dry-run server path checker for LoReflection.

The checker reads a .env-style path file and reports whether required
repositories, datasets, model directories, and output paths are configured.
It does not load data, download models, run inference, or start training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_VARIABLES = [
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

STAGE_HINTS = {
    "LOREFLECTION_ROOT": "all stages",
    "SEMLAYOUTDIFF_ROOT": "Step 3 val50 architecture/semantic conversion",
    "EDITROOM_ROOT": "Step 3 editing pair conversion",
    "DIFFSYNTH_ROOT": "DiffSynth inpaint LoRA training",
    "QWEN_VL_REPO": "Qwen-VL SFT training",
    "THREED_FRONT_ROOT": "real 3D-FRONT data conversion",
    "THREED_FUTURE_ROOT": "real 3D-FUTURE asset/category mapping",
    "QWEN25_VL_MODEL_PATH": "Qwen2.5-VL planner/reviewer training or inference",
    "QWEN_IMAGE_MODEL_PATH": "Qwen-Image generation/inpainting",
    "DIFFSYNTH_INPAINT_MODEL_PATH": "DiffSynth Qwen-Image inpaint training/inference",
    "INSTANTX_INPAINT_MODEL_PATH": "InstantX zero-shot baseline",
    "OUTPUT_ROOT": "server artifact output",
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


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path("server_configs/paths.template.env"), help=".env-style path file.")
    parser.add_argument("--report", type=Path, default=Path("reports/server_path_check_report.json"), help="JSON report path.")
    parser.add_argument("--strict", action="store_true", help="Mark missing real paths as warnings; template placeholders are not fatal.")
    args = parser.parse_args()

    values = read_env(args.env_file)
    checks = {}
    warnings = []
    for key in REQUIRED_VARIABLES:
        value = values.get(key, "")
        configured = bool(value)
        placeholder = is_placeholder(value)
        exists = Path(value).exists() if configured and not placeholder else False
        note = "configured"
        if not configured:
            note = "missing value"
            warnings.append(f"{key} is not configured.")
        elif placeholder:
            note = "placeholder path; fill this on the server before real runs"
            warnings.append(f"{key} still uses a template placeholder.")
        elif not exists:
            note = "path does not exist on this machine"
            warnings.append(f"{key} path does not exist: {value}")
        checks[key] = {
            "value": value,
            "configured": "yes" if configured else "no",
            "exists": "yes" if exists else "no",
            "required_for_stage": STAGE_HINTS[key],
            "note": note,
        }

    report = {
        "schema_version": "server-path-check-report-v1",
        "env_file": args.env_file.as_posix(),
        "strict": args.strict,
        "checks": checks,
        "warnings": warnings,
        "fatal_errors": [],
        "dry_run": True,
        "message": "This is a dry-run path check. No model or data was loaded.",
    }
    write_json(args.report, report)
    print("This is a dry-run path check. No model or data was loaded.")
    print(f"Wrote server path check report to {args.report}")
    if warnings:
        print(f"Warnings: {len(warnings)} placeholder or missing path item(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
