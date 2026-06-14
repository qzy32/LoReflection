#!/usr/bin/env python
"""Compute toy editing preservation metrics from old/new eval representations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-eval-json", required=True, type=Path, help="Old eval representation JSON.")
    parser.add_argument("--new-eval-json", required=True, type=Path, help="New eval representation JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Metric JSON output.")
    args = parser.parse_args()
    old = json.loads(args.old_eval_json.read_text(encoding="utf-8"))
    new = json.loads(args.new_eval_json.read_text(encoding="utf-8"))
    metrics = {"object_count_delta": len(new.get("objects", [])) - len(old.get("objects", []))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote editing metrics to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

