
from __future__ import annotations
import copy
from typing import Any

FORBIDDEN_TERMS = ["center_m", "size_m", "orientation_deg", "bbox_px", "footprint_m", "metric_transform", "source_json_path", "px", "pixel", "meter", "cm", "coordinate"]
GEOMETRY_KEYS = {"center_m", "size_m", "orientation_deg", "bbox_px", "bbox_m", "footprint_m", "footprint_px", "metric_transform", "source_json_path", "source_object_id"}


def strip_geometry(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: strip_geometry(v) for k, v in value.items() if k not in GEOMETRY_KEYS}
    if isinstance(value, list):
        return [strip_geometry(v) for v in value]
    return value


def build_goal_aligned_llm_request(scene_facts: dict[str, Any], goal_lostate_rich: dict[str, Any], relation_triplets: list[dict[str, Any]], placement_order: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "room_type": scene_facts.get("room_type", "unknown"),
        "furniture_counts": scene_facts.get("furniture_counts", {}),
        "goal_lostate_rich_without_geometry": strip_geometry(goal_lostate_rich),
        "relation_triplets": relation_triplets,
        "placement_order": placement_order,
        "architecture_facts": scene_facts.get("architecture_facts", {}),
        "forbidden_terms": FORBIDDEN_TERMS,
    }
    return {
        "sample_id": scene_facts.get("sample_id"),
        "system": "You generate coordinate-free indoor semantic layout prompts. Return strict JSON only. Do not mention coordinates, sizes, pixels, meters, source paths, hidden IDs, colors, materials, style, or appearance.",
        "user": payload,
        "required_output_schema": {
            "entity_summary": "string",
            "placement_order_summary": "string",
            "relation_summary": "string",
            "constraint_summary": "string",
            "prompt_llm_functional": "Context_Control. string",
            "prompt_llm_relation_rich": "Context_Control. string",
        },
    }


def deterministic_goal_aligned_output(scene_facts: dict[str, Any], relation_triplets: list[dict[str, Any]], placement_order: dict[str, Any]) -> dict[str, str]:
    counts = scene_facts.get("furniture_counts", {})
    room = scene_facts.get("room_type") or "room"
    slots = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    rels = "; ".join(f"{r['subject']} {r['predicate']} {r['object']}" for r in relation_triplets[:4])
    arch = "Follow the architecture condition image and keep furniture inside the room with clear door and window circulation."
    functional = f"Context_Control. Create a top-down fixed-palette semantic {room} layout with {slots}. {arch} Use only the required furniture categories."
    rich = f"Context_Control. Create a top-down fixed-palette semantic {room} layout with {slots}. {placement_order.get('placement_order_summary','Arrange the main furniture first.')} Respect these layout relations: {rels}. {arch}"
    return {
        "entity_summary": f"{room} with {slots}",
        "placement_order_summary": placement_order.get("placement_order_summary", "Arrange main furniture first."),
        "relation_summary": rels,
        "constraint_summary": arch,
        "prompt_llm_functional": functional,
        "prompt_llm_relation_rich": rich,
    }
