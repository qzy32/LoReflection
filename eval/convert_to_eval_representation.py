#!/usr/bin/env python
"""Convert Observed LoState into the minimal LoReflection eval representation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def convert(observed_lostate: dict, sample_id: str) -> dict:
    return {
        "schema_version": "eval-representation-v1",
        "sample_id": sample_id,
        "room_type": observed_lostate.get("room_type", "room"),
        "objects": observed_lostate.get("furniture_instances", []),
        "relations": observed_lostate.get("measured_relations", []),
        "metrics": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed-lostate", required=True, type=Path, help="Observed LoState JSON.")
    parser.add_argument("--sample-id", default=None, help="Eval sample id.")
    parser.add_argument("--output", required=True, type=Path, help="Output eval representation JSON.")
    args = parser.parse_args()
    observed = load_json(args.observed_lostate)
    sample_id = args.sample_id or observed.get("metadata", {}).get("task_id", args.observed_lostate.stem)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(convert(observed, sample_id), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote eval representation to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

