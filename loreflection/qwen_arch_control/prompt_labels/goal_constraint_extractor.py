from __future__ import annotations

from typing import Any


def build_rich_goal_lostate(scene_facts: dict[str, Any], architecture_ref: str) -> dict[str, Any]:
    slots = []
    for category, count in scene_facts.get("furniture_counts", {}).items():
        slots.append({"slot_id": f"slot_{category}", "category": category, "required": True, "count": int(count)})
    return {
        "schema_version": "goal-lostate-rich-v1",
        "state_role": "goal",
        "sample_id": scene_facts.get("sample_id"),
        "room_type": scene_facts.get("room_type"),
        "furniture_slots": slots,
        "required_counts": scene_facts.get("furniture_counts", {}),
        "pairwise_constraints": scene_facts.get("relation_facts", []),
        "global_constraints": scene_facts.get("global_constraints", []),
        "architecture_condition_ref": architecture_ref,
    }


def assert_no_geometry(goal: dict[str, Any]) -> None:
    banned = {"center_m", "size_m", "orientation_deg", "bbox_px", "footprint_m", "source_json_path", "metric_transform"}
    text = str(goal)
    found = [term for term in banned if term in text]
    if found:
        raise ValueError(f"rich Goal LoState contains geometry/provenance terms: {found}")
