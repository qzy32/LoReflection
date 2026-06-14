#!/usr/bin/env python
"""Build LoReflection RepairPlan from an EditRoom-like before/after edit pair."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_mask_spec_from_editroom_pair import find_deleted_target, find_existing_target, find_insert_target, load_json, objects_by_id


ACTION_MAP = {"INSERT": "INSERT", "DELETE": "DELETE", "REPLACE": "REPLACE", "MOVE": "MOVE"}


def category_phrase(objects: list[dict]) -> str:
    if not objects:
        return "all non-target furniture"
    return ", ".join(obj.get("category", obj["instance_id"]) for obj in objects)


def target_for_edit(before: dict, after: dict, instruction: dict) -> dict:
    edit_type = instruction["edit_type"].upper()
    if edit_type == "INSERT":
        return find_insert_target(before, after, instruction)
    if edit_type == "DELETE":
        return find_deleted_target(before, after, instruction)
    before_target, after_target = find_existing_target(before, after, instruction)
    return after_target if edit_type == "MOVE" else before_target


def protected_refs(before: dict, target_ref: str) -> list[str]:
    return [obj["instance_id"] for obj in before.get("objects", []) if obj["instance_id"] != target_ref]


def correction_prompt(before: dict, after: dict, instruction: dict, target: dict, protected: list[str]) -> str:
    room_type = instruction.get("room_type") or after.get("room_type") or before.get("room_type", "room")
    edit_type = instruction["edit_type"].upper()
    target_category = target.get("category", instruction.get("target_category", "target object"))
    relation = instruction.get("target_relation", {})
    relation_text = ""
    if relation:
        relation_text = f" {relation.get('predicate', 'near')} {relation.get('object', 'the referenced object')}"
    protected_objects = [obj for obj in before.get("objects", []) if obj["instance_id"] in set(protected)]
    preserved = category_phrase(protected_objects)
    if edit_type == "DELETE":
        target_state = "the masked region is restored to empty traversable floor space"
    else:
        target_state = f"the masked region contains one {target_category}{relation_text}"
    return (
        f"A top-down fixed-palette semantic {room_type} layout where {target_state}. "
        f"The {preserved}, walls, door clearance, and all furniture outside the mask remain unchanged. "
        "No new collision, out-of-bound placement, or door/window blocking."
    )


def build_repairplan(before: dict, after: dict, instruction: dict, mask_spec: dict) -> dict:
    edit_type = instruction.get("edit_type", "").upper()
    if edit_type not in ACTION_MAP:
        raise ValueError(f"Unsupported edit_type {edit_type!r}. Supported: {sorted(ACTION_MAP)}")
    target = target_for_edit(before, after, instruction)
    target_ref = target["instance_id"]
    protected = protected_refs(before, target_ref)
    prompt = correction_prompt(before, after, instruction, target, protected)
    edit_id = instruction.get("edit_id", "edit_unknown")
    return {
        "schema_version": "repairplan-v1",
        "repair_plan_id": f"repairplan_{edit_id}",
        "task_id": edit_id,
        "repair_round": 0,
        "action_type": ACTION_MAP[edit_type],
        "target_ref": target_ref,
        "protected_refs": protected,
        "mask_spec": mask_spec,
        "correction_prompt": prompt,
        "negative_prompt": "photorealistic texture, perspective view, shadows, labels, text",
        "acceptance_criteria": ["target_resolved", "no_collision", "no_oob", "non_target_preservation"],
        "source": {"adapter": "EditRoom toy adapter", "instruction": instruction.get("instruction", "")},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-layout", required=True, type=Path, help="EditRoom-like before layout JSON.")
    parser.add_argument("--after-layout", required=True, type=Path, help="EditRoom-like after layout JSON.")
    parser.add_argument("--edit-instruction", required=True, type=Path, help="Edit instruction JSON.")
    parser.add_argument("--mask-spec", required=True, type=Path, help="LoReflection mask_spec JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output RepairPlan JSON.")
    args = parser.parse_args()

    repairplan = build_repairplan(
        load_json(args.before_layout),
        load_json(args.after_layout),
        load_json(args.edit_instruction),
        load_json(args.mask_spec),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(repairplan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote RepairPlan to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

