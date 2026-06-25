#!/usr/bin/env python3
"""Validate observer round-trip reports produced by U1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-report", type=Path, default=Path("reports/synthetic_observer_roundtrip.json"))
    parser.add_argument("--real-report", type=Path, default=Path("reports/real_scene_observer_roundtrip.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/observer_roundtrip_validation.json"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    synthetic = json.loads(args.synthetic_report.read_text(encoding="utf-8")) if args.synthetic_report.exists() else {}
    real = json.loads(args.real_report.read_text(encoding="utf-8")) if args.real_report.exists() else {}
    failures = []
    if synthetic.get("A_all_categories", {}).get("category_accuracy") != 1.0:
        failures.append("synthetic all-category decode failed")
    if synthetic.get("D_touching", {}).get("merge") is True:
        failures.append("same-class touching merge detected")
    if real.get("instance_count_accuracy", 0) < 0.99:
        failures.append("real-scene instance count accuracy below 99%")
    report = {"synthetic": synthetic, "real": real, "failures": failures, "strict_validation": not failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
