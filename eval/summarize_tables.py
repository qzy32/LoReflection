#!/usr/bin/env python
"""Summarize metric JSON files into a compact CSV table."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-dir", required=True, type=Path, help="Directory containing metric JSON files.")
    parser.add_argument("--output", required=True, type=Path, help="Output CSV table.")
    args = parser.parse_args()
    rows = []
    for path in sorted(args.metrics_dir.rglob("*.json")):
        metrics = json.loads(path.read_text(encoding="utf-8"))
        row = {"file": str(path)}
        row.update({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in metrics.items()})
        rows.append(row)
    fieldnames = sorted({key for row in rows for key in row.keys()}) if rows else ["file"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote summary table to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

