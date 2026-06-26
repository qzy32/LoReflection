"""Extract a geometry-free Goal LoState v2 label from real layout data."""

from __future__ import annotations

from collections import Counter
from typing import Any

from loreflection.semantic_registry import SemanticRegistry, load_registry


def extract_goal_lostate(
    layout: dict[str, Any],
    architecture: dict[str, Any],
    registry: SemanticRegistry | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    counts = Counter(str(obj["category"]) for obj in layout.get("objects", []))
    slots = [
        {
            "slot_id": f"goal:{category}",
            "category": category,
            "category_id": registry.name_to_id[category],
            "required": True,
            "count": count,
            "role": "required_furniture",
            "source": "layout_json_category_count",
            "numeric_pose": None,
        }
        for category, count in sorted(counts.items())
    ]
    constraints = [
        {
            "constraint_id": f"require_{category}",
            "constraint_kind": "requirement",
            "domain": "object",
            "necessity": "required",
            "prompt_hint": f"Include the required {category}.",
            "verification": {"type": "category_count", "category": category, "count": count},
        }
        for category, count in sorted(counts.items())
    ]
    constraints.extend(
        [
            {
                "constraint_id": "inside_room",
                "constraint_kind": "global",
                "domain": "global",
                "necessity": "required",
                "prompt_hint": "Keep all furniture inside the room.",
                "verification": {"type": "inside_room"},
            },
            {
                "constraint_id": "avoid_overlap",
                "constraint_kind": "global",
                "domain": "global",
                "necessity": "required",
                "prompt_hint": "Avoid furniture overlap.",
                "verification": {"type": "pairwise_overlap"},
            },
            {
                "constraint_id": "palette_exact",
                "constraint_kind": "global",
                "domain": "global",
                "necessity": "required",
                "prompt_hint": "Use only the frozen semantic palette.",
                "verification": {"type": "palette_exact"},
            },
        ]
    )
    anchor_types = {str(anchor.get("anchor_type")) for anchor in architecture.get("anchors", [])}
    for anchor_type in ("door", "window"):
        if anchor_type in anchor_types:
            constraints.append(
                {
                    "constraint_id": f"{anchor_type}_clearance_free",
                    "constraint_kind": "region",
                    "domain": "object_region",
                    "necessity": "required",
                    "prompt_hint": f"Keep the {anchor_type} clearance area free.",
                    "verification": {"type": "architecture_clearance", "anchor_type": anchor_type},
                }
            )
    return {
        "schema_version": "goal-lostate-v2",
        "state_role": "goal",
        "metadata": {
            "task_id": layout["sample_id"],
            "source_kind": layout.get("source", {}).get("kind", "unknown"),
        },
        "architecture_ref": {"architecture_id": architecture["architecture_id"]},
        "semantic_registry_ref": {
            "registry_id": "semantic_registry_v2",
            "registry_hash": registry.registry_hash,
        },
        "room_type": layout.get("room_type") or "room",
        "furniture_slots": slots,
        "goal_constraints": constraints,
        "verification_profile": {
            "required_checks": [
                "inside_room",
                "avoid_overlap",
                "palette_exact",
                "object_count",
            ]
        },
        "prompt_compilation_policy": {
            "include_optional_slots": False,
            "include_preferred_constraints": True,
            "geometry_in_prompt": False,
        },
    }
