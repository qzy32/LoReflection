#!/usr/bin/env python
"""Build a ControlNet repair-pair manifest for DiffSynth export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-image", required=True, help="Target/clean semantic layout image.")
    parser.add_argument("--control-image", required=True, help="Bad/current semantic layout image.")
    parser.add_argument("--control-mask", required=True, help="Binary control mask image.")
    parser.add_argument("--repairplan", required=True, type=Path, help="RepairPlan JSON containing correction_prompt.")
    parser.add_argument("--sample-id", default="toy_repair_001", help="Sample id.")
    parser.add_argument("--output", required=True, type=Path, help="Output train.json manifest.")
    args = parser.parse_args()
    repairplan = load_json(args.repairplan)
    sample = {
        "schema_version": "controlnet-sample-v1",
        "sample_id": args.sample_id,
        "target_image": args.target_image,
        "control_image": args.control_image,
        "control_mask": args.control_mask,
        "correction_prompt": repairplan["correction_prompt"],
        "repair_plan": str(args.repairplan),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema_version": "controlnet-repair-manifest-v1", "samples": [sample]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote ControlNet repair-pair manifest to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
