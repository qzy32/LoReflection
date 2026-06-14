#!/usr/bin/env python
"""Build a LoReview from Goal and Observed LoState with local placeholder reviewers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.loram import align
from runtime.track_a_geometry_review import review_geometry
from runtime.track_b_semantic_review import semantic_review_stub


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_review(goal: dict, observed: dict) -> dict:
    alignment = align(goal, observed)
    issues = review_geometry(goal, observed, alignment) + semantic_review_stub(goal, observed)
    task_id = goal.get("metadata", {}).get("task_id", "unknown_task")
    repair_round = observed.get("metadata", {}).get("repair_round", 0)
    return {
        "schema_version": "loreview-v1",
        "review_id": f"review_{task_id}_round{repair_round}",
        "task_id": task_id,
        "repair_round": repair_round,
        "alignment": alignment,
        "issues": issues,
        "summary": {"num_issues": len(issues), "num_hard": sum(1 for i in issues if i.get("severity") == "error")},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-lostate", required=True, type=Path, help="Goal LoState JSON.")
    parser.add_argument("--observed-lostate", required=True, type=Path, help="Observed LoState JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output LoReview JSON.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_review(load_json(args.goal_lostate), load_json(args.observed_lostate)), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote LoReview to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

