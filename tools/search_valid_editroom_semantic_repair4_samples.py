#!/usr/bin/env python3
"""Search valid current semantic_repair4 samples from real EditRoom pairs.

This is a lightweight entry point for C12.1. The heavy scan is intended to run
on the A800 server where the real EditRoom dataset is mounted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="reports/c12_1_candidate_search_summary.csv")
    parser.add_argument("--report", default="reports/c12_1_noop_replacement_report.json")
    args = parser.parse_args()
    report = Path(args.report)
    if report.exists():
        data = json.loads(report.read_text(encoding="utf-8"))
        print(json.dumps({"status": data.get("result"), "report": str(report)}, ensure_ascii=False))
        return 0
    raise SystemExit(
        "Run the C12.1 remote search from Codex/A800 first; "
        f"expected report is missing: {report}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
