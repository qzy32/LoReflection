#!/usr/bin/env python
"""Compute toy reflection-loop metrics from LoReview JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def issue_count(path: Path) -> int:
    return len(json.loads(path.read_text(encoding="utf-8")).get("issues", []))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", nargs="+", required=True, type=Path, help="LoReview JSON files in loop order.")
    parser.add_argument("--output", required=True, type=Path, help="Metric JSON output.")
    args = parser.parse_args()
    counts = [issue_count(path) for path in args.reviews]
    metrics = {"issue_counts": counts, "final_issue_count": counts[-1] if counts else None}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote reflection metrics to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

