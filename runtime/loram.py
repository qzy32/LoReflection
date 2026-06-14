#!/usr/bin/env python
"""Minimal LoRAM slot-instance alignment scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def align(goal_lostate: dict, observed_lostate: dict) -> list[dict]:
    """Create simple exact-category slot to instance alignments."""
    remaining = list(observed_lostate.get("furniture_instances", []))
    rows = []
    for slot in goal_lostate.get("furniture_slots", []):
        match = next((inst for inst in remaining if inst.get("category") == slot.get("category")), None)
        if match:
            remaining.remove(match)
            rows.append({"slot_id": slot["slot_id"], "instance_id": match["instance_id"], "match_type": "exact"})
        else:
            rows.append({"slot_id": slot["slot_id"], "instance_id": None, "match_type": "missing"})
    for inst in remaining:
        rows.append({"slot_id": None, "instance_id": inst["instance_id"], "match_type": "extra"})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-lostate", required=True, type=Path, help="Goal LoState JSON.")
    parser.add_argument("--observed-lostate", required=True, type=Path, help="Observed LoState JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Alignment JSON output.")
    args = parser.parse_args()
    rows = align(load_json(args.goal_lostate), load_json(args.observed_lostate))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"alignment": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote LoRAM alignment to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

