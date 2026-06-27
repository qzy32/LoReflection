#!/usr/bin/env python
"""Run a no-model LoReflection closed-loop smoke pass."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.loram import align
from loreflection.goal.prompt_package_validator import ERROR_CLIENT_MISSING, PromptCompilerError
from runtime.track_a_geometry_review import review_geometry
from runtime.track_b_semantic_review import semantic_review_stub


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--architecture", required=True, type=Path, help="Architecture JSON.")
    parser.add_argument("--goal-lostate", required=True, type=Path, help="Goal LoState JSON.")
    parser.add_argument("--observed-lostate", required=True, type=Path, help="Observed LoState JSON.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for smoke outputs.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    arch = load_json(args.architecture)
    goal = load_json(args.goal_lostate)
    observed = load_json(args.observed_lostate)
    raise PromptCompilerError(ERROR_CLIENT_MISSING, "runtime closed-loop smoke requires an upstream LLM PromptPackage")
    alignment = align(goal, observed)
    issues = review_geometry(goal, observed, alignment) + semantic_review_stub(goal, observed)
    review = {
        "schema_version": "loreview-v1",
        "review_id": f"review_{goal['metadata']['task_id']}_round0",
        "task_id": goal["metadata"]["task_id"],
        "repair_round": 0,
        "alignment": alignment,
        "issues": issues,
        "summary": {"num_issues": len(issues), "num_hard": sum(1 for i in issues if i["severity"] == "error")},
    }
    (args.output_dir / "prompt_package_v1.json").write_text(json.dumps(prompt, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "loreview_v1.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote closed-loop smoke outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

