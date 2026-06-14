#!/usr/bin/env python
"""Build a toy Goal LoState from user instruction and Architecture JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_goal(architecture: dict, task_id: str, instruction: str) -> dict:
    return {
        "schema_version": "goal-lostate-v1",
        "state_role": "goal",
        "metadata": {"task_id": task_id, "repair_round": 0, "created_by": "local_rule_based_skeleton", "user_instruction": instruction},
        "architecture_ref": {"architecture_id": architecture["architecture_id"], "coordinate_transform_id": "xz_to_image_001"},
        "semantic_registry_ref": {
            "palette_id": "indoor_palette_v1",
            "category_set": "indoor_furniture_categories_v1",
            "relation_set": "layout_relations_v1",
        },
        "room_type": architecture.get("room_type", "bedroom"),
        "furniture_slots": [
            {"slot_id": "slot_bed_1", "category": "bed", "category_id": 5, "required": True, "count": 1, "generation_hints": [{"description": "against a wall away from the door", "anchor_refs": ["arch:door_001"]}], "avoid_refs": ["arch:door_001_clearance"], "source": "user_instruction"},
            {"slot_id": "slot_nightstand_1", "category": "nightstand", "category_id": 9, "required": True, "count": 1, "generation_hints": [{"description": "beside the bed", "anchor_refs": ["slot_bed_1"]}], "avoid_refs": [], "source": "room_prior"},
        ],
        "desired_relations": [
            {"relation_id": "dr_nightstand_bed", "subject": "slot_nightstand_1", "predicate": "adjacent_to", "object": "slot_bed_1", "object_kind": "furniture_slot", "params": {"max_distance_m": 0.5}, "necessity": "required", "verification": "geometric_then_semantic", "source": "room_prior"}
        ],
        "verification_profile": {"hard_checks": [{"check_id": "hc_count_match", "type": "count_match", "scope": "furniture_slots", "severity": "error"}]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--architecture", required=True, type=Path, help="Input Architecture JSON.")
    parser.add_argument("--instruction", default="Create a bedroom with one bed and one nightstand.", help="User instruction.")
    parser.add_argument("--task-id", default="toy_bedroom_001", help="Task id.")
    parser.add_argument("--output", required=True, type=Path, help="Output Goal LoState JSON.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_goal(load_json(args.architecture), args.task_id, args.instruction), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote Goal LoState to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

