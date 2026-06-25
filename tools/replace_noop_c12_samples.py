#!/usr/bin/env python3
"""Replace failed C12 no-op rows once C12.1 replacements are available."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replacement-report", default="reports/c12_1_noop_replacement_report.json")
    parser.add_argument("--manifest", default="reports/current_c12_input_manifest.json")
    args = parser.parse_args()
    report_path = Path(args.replacement_report)
    manifest_path = Path(args.manifest)
    if not report_path.exists():
        raise SystemExit(f"missing replacement report: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("result") != "PASS":
        raise SystemExit(f"replacement report is not PASS: {report.get('result')}")
    if not manifest_path.exists():
        raise SystemExit(f"missing manifest: {manifest_path}")
    print(json.dumps({"status": "manifest_already_rebuilt_by_c12_1", "manifest": str(manifest_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
