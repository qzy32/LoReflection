#!/usr/bin/env python
"""Compute toy geometry metrics from eval representation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-json", required=True, type=Path, help="Eval representation JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Metric JSON output.")
    args = parser.parse_args()
    data = json.loads(args.eval_json.read_text(encoding="utf-8"))
    metrics = {"num_bboxes": sum(1 for obj in data.get("objects", []) if "bbox_px" in obj), "geometry_valid": True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote geometry metrics to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

