from loreflection.goal.prompt_compiler import compile_prompt_package
from loreflection.goal.prompt_compiler_llm import build_architecture_summary


def goal():
    return {
        "metadata": {"task_id": "t1"},
        "room_type": "bedroom",
        "furniture_slots": [
            {"slot_id": "goal:bed", "category": "double_bed", "count": 1, "required": True, "role": "sleeping"},
            {"slot_id": "goal:wardrobe", "category": "wardrobe", "count": 1, "required": True, "role": "storage"},
        ],
        "goal_constraints": [
            {"constraint_id": "inside_room", "constraint_kind": "global", "necessity": "required", "prompt_hint": "Keep furniture inside the room floor region."}
        ],
        "prompt_compilation_policy": {},
    }


class GoodClient:
    def generate_json(self, system_prompt, user_payload):
        return {
            "compiled_text_prompt": "Context_Control. Create a top-down fixed-palette semantic bedroom layout with one double_bed and one wardrobe. Architecture_Control. Use the architecture condition image for the room floor boundary and visible doors. Palette_Control. Use only the frozen semantic categories and palette. Active semantic categories: double_bed, wardrobe.",
            "used_slot_ids": ["goal:bed", "goal:wardrobe"],
            "used_constraint_ids": ["inside_room"],
            "omitted_constraint_ids": [],
            "architecture_claims": ["room_floor_boundary", "visible_door"],
            "notes": [],
        }


def test_llm_compiler_accepts_valid_json():
    arch = build_architecture_summary({"door_anchor_count": 1, "window_anchor_count": 0})
    pkg = compile_prompt_package(goal(), architecture_summary=arch, llm_client=GoodClient(), mode="llm_with_rule_fallback")
    assert pkg["llm_prompt_compiler_report"]["used_llm"] is True
    assert pkg["llm_prompt_compiler_report"]["fallback_used"] is False
    assert "double_bed" in pkg["compiled_text_prompt"]
