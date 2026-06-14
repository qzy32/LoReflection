#!/usr/bin/env python
"""Build a Planner SFT manifest from local LoReflection artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Current bad semantic layout image path.")
    parser.add_argument("--goal-lostate", required=True, help="Goal LoState JSON path.")
    parser.add_argument("--observed-lostate", required=True, help="Observed LoState JSON path.")
    parser.add_argument("--loreview", required=True, help="LoReview JSON path.")
    parser.add_argument("--repairplan", required=True, help="RepairPlan JSON path.")
    parser.add_argument("--sample-id", default="toy_planner_001", help="Sample id.")
    parser.add_argument("--instruction", default="Plan one local layout repair.", help="Planner instruction.")
    parser.add_argument("--output", required=True, type=Path, help="Output planner SFT manifest JSON.")
    args = parser.parse_args()
    manifest = {
        "schema_version": "planner-sft-manifest-v1",
        "samples": [
            {
                "sample_id": args.sample_id,
                "image": args.image,
                "instruction": args.instruction,
                "goal_lostate": args.goal_lostate,
                "observed_lostate": args.observed_lostate,
                "loreview": args.loreview,
                "repairplan": args.repairplan,
            }
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote Planner SFT manifest to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
