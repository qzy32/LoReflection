#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def large_training_allowed(alignment_report: dict, smoke_report: dict) -> bool:
    return bool(
        alignment_report.get("critical_gates_pass")
        and smoke_report.get("smoke_pass")
        and smoke_report.get("palette_unknown_rate_after_quantization") == 0.0
        and smoke_report.get("architecture_preservation_accuracy", 0.0) >= 0.95
        and smoke_report.get("furniture_pixel_f1", 0.0) >= 0.35
        and smoke_report.get("forbidden_architecture_overwrite_rate", 1.0) <= 0.005
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate large Qwen training on alignment and smoke reports.")
    parser.add_argument("--alignment-report", type=Path, required=True)
    parser.add_argument("--smoke-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    alignment = json.loads(args.alignment_report.read_text(encoding="utf-8"))
    smoke = json.loads(args.smoke_report.read_text(encoding="utf-8"))
    report = {
        "alignment_critical_gates_pass": alignment.get("critical_gates_pass"),
        "smoke_pass": smoke.get("smoke_pass"),
        "large_training_allowed": large_training_allowed(alignment, smoke),
        "blocking_reason": None,
    }
    if not report["large_training_allowed"]:
        report["blocking_reason"] = "alignment or smoke gate failed; do not launch large training"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["large_training_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
