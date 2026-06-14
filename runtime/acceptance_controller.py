#!/usr/bin/env python
"""AcceptanceController scaffold for repair-loop accept/reject decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def cost(review: dict) -> tuple[int, int, int]:
    issues = review.get("issues", [])
    hard = sum(1 for i in issues if i.get("severity") == "error")
    warnings = sum(1 for i in issues if i.get("severity") == "warning")
    info = sum(1 for i in issues if i.get("severity") == "info")
    return hard, warnings, info


def decide(old_review: dict, new_review: dict) -> dict:
    old_cost = cost(old_review)
    new_cost = cost(new_review)
    accepted = new_cost < old_cost and new_cost[0] == 0
    return {
        "decision": "accept" if accepted else "reject",
        "old_cost": old_cost,
        "new_cost": new_cost,
        "reason": "lexicographic cost decreased with no hard violations" if accepted else "acceptance criteria not met",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-review", required=True, type=Path, help="Previous LoReview JSON.")
    parser.add_argument("--new-review", required=True, type=Path, help="New LoReview JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Acceptance decision JSON.")
    args = parser.parse_args()
    result = decide(load_json(args.old_review), load_json(args.new_review))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote acceptance decision to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

