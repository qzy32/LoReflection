#!/usr/bin/env python
"""Build LoReflection mask_spec from an EditRoom-like before/after edit pair."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SUPPORTED_EDIT_TYPES = {"INSERT", "DELETE", "REPLACE", "MOVE"}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def objects_by_id(layout: dict) -> dict[str, dict]:
    return {obj["instance_id"]: obj for obj in layout.get("objects", [])}


def find_insert_target(before: dict, after: dict, instruction: dict) -> dict:
    before_ids = set(objects_by_id(before))
    after_objects = objects_by_id(after)
    target_ref = instruction.get("target_ref")
    if target_ref and target_ref in after_objects and target_ref not in before_ids:
        return after_objects[target_ref]
    target_category = instruction.get("target_category")
    candidates = [obj for obj in after_objects.values() if obj["instance_id"] not in before_ids]
    if target_category:
        candidates = [obj for obj in candidates if obj.get("category") == target_category]
    if not candidates:
        raise ValueError("INSERT edit has no newly inserted object in after_layout.")
    return candidates[0]


def find_deleted_target(before: dict, after: dict, instruction: dict) -> dict:
    before_objects = objects_by_id(before)
    after_ids = set(objects_by_id(after))
    target_ref = instruction.get("target_ref")
    if target_ref and target_ref in before_objects and target_ref not in after_ids:
        return before_objects[target_ref]
    candidates = [obj for obj in before_objects.values() if obj["instance_id"] not in after_ids]
    if not candidates:
        raise ValueError("DELETE edit has no deleted object in before_layout.")
    return candidates[0]


def find_existing_target(before: dict, after: dict, instruction: dict) -> tuple[dict, dict]:
    before_objects = objects_by_id(before)
    after_objects = objects_by_id(after)
    target_ref = instruction.get("target_ref")
    if target_ref and target_ref in before_objects and target_ref in after_objects:
        return before_objects[target_ref], after_objects[target_ref]
    shared_ids = sorted(set(before_objects) & set(after_objects))
    for instance_id in shared_ids:
        before_obj = before_objects[instance_id]
        after_obj = after_objects[instance_id]
        if before_obj.get("bbox_px") != after_obj.get("bbox_px") or before_obj.get("category") != after_obj.get("category"):
            return before_obj, after_obj
    raise ValueError("MOVE/REPLACE edit has no changed shared target object.")


def build_mask_spec(before: dict, after: dict, instruction: dict) -> dict:
    edit_type = instruction.get("edit_type", "").upper()
    if edit_type not in SUPPORTED_EDIT_TYPES:
        raise ValueError(f"Unsupported edit_type {edit_type!r}. Supported: {sorted(SUPPORTED_EDIT_TYPES)}")
    image_size = after.get("image_size_px") or before.get("image_size_px") or [1024, 1024]
    edit_id = instruction.get("edit_id", "edit_unknown")
    item: dict
    if edit_type == "INSERT":
        target = find_insert_target(before, after, instruction)
        item = {"type": "bbox", "bbox_px": target["bbox_px"], "value": 255}
    elif edit_type == "DELETE":
        target = find_deleted_target(before, after, instruction)
        item = {"type": "instance_ref", "instance_ref": target["instance_id"], "value": 255}
    elif edit_type == "REPLACE":
        before_target, _ = find_existing_target(before, after, instruction)
        item = {"type": "instance_ref", "instance_ref": before_target["instance_id"], "value": 255}
    else:
        before_target, after_target = find_existing_target(before, after, instruction)
        item = {
            "type": "old_new_union",
            "old_bbox_px": before_target["bbox_px"],
            "new_bbox_px": after_target["bbox_px"],
            "value": 255,
        }
    return {
        "schema_version": "mask-spec-v1",
        "mask_id": f"mask_{edit_id}",
        "image_size_px": image_size,
        "items": [item],
        "source": {"adapter": "EditRoom toy adapter", "edit_type": edit_type},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-layout", required=True, type=Path, help="EditRoom-like before layout JSON.")
    parser.add_argument("--after-layout", required=True, type=Path, help="EditRoom-like after layout JSON.")
    parser.add_argument("--edit-instruction", required=True, type=Path, help="Edit instruction JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output LoReflection mask_spec JSON.")
    args = parser.parse_args()

    mask_spec = build_mask_spec(load_json(args.before_layout), load_json(args.after_layout), load_json(args.edit_instruction))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(mask_spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote mask_spec to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

