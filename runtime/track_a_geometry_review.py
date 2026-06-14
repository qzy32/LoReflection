#!/usr/bin/env python
"""Track-A programmatic geometry review scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def review_geometry(goal_lostate: dict, observed_lostate: dict, alignment: list[dict]) -> list[dict]:
    """Emit count/missing/extra issues from LoRAM alignment."""
    issues = []
    for row in alignment:
        if row["match_type"] == "missing":
            issues.append(
                {
                    "issue_id": f"missing_{row['slot_id']}",
                    "issue_type": "entity_missing",
                    "severity": "error",
                    "target_ref": row["slot_id"],
                    "recommended_action_type": "INSERT",
                    "track": "A",
                }
            )
        elif row["match_type"] == "extra":
            issues.append(
                {
                    "issue_id": f"extra_{row['instance_id']}",
                    "issue_type": "entity_extra",
                    "severity": "warning",
                    "target_ref": row["instance_id"],
                    "recommended_action_type": "DELETE",
                    "track": "A",
                }
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-lostate", required=True, type=Path, help="Goal LoState JSON.")
    parser.add_argument("--observed-lostate", required=True, type=Path, help="Observed LoState JSON.")
    parser.add_argument("--alignment", required=True, type=Path, help="LoRAM alignment JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Track-A issues JSON.")
    args = parser.parse_args()
    alignment = load_json(args.alignment)["alignment"]
    issues = review_geometry(load_json(args.goal_lostate), load_json(args.observed_lostate), alignment)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"issues": issues}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote Track-A review to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
