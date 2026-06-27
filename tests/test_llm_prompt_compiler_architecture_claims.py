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


class BadWallClient:
    def generate_json(self, system_prompt, user_payload):
        return {
            "compiled_text_prompt": "Context_Control. Create a bedroom with one double_bed. Architecture_Control. The walls are visible in the architecture image. Palette_Control. Active semantic categories: double_bed, wardrobe.",
            "used_slot_ids": ["goal:bed"],
            "used_constraint_ids": [],
            "omitted_constraint_ids": ["inside_room"],
            "architecture_claims": ["visible_wall"],
            "notes": [],
        }


class BadGeometryClient:
    def generate_json(self, system_prompt, user_payload):
        return {
            "compiled_text_prompt": "Context_Control. Place the double_bed at center_m [1, 2]. Architecture_Control. Use visible doors. Palette_Control. Active semantic categories: double_bed, wardrobe.",
            "used_slot_ids": ["goal:bed"],
            "used_constraint_ids": [],
            "omitted_constraint_ids": ["inside_room"],
            "architecture_claims": ["room_floor_boundary"],
            "notes": [],
        }


def test_llm_wall_claim_falls_back_when_wall_not_visible():
    arch = build_architecture_summary({"door_anchor_count": 1, "window_anchor_count": 0})
    pkg = compile_prompt_package(goal(), architecture_summary=arch, llm_client=BadWallClient(), mode="llm_with_rule_fallback")
    assert pkg["llm_prompt_compiler_report"]["fallback_used"] is True
    assert "walls are visible" not in pkg["compiled_text_prompt"]


def test_llm_geometry_leakage_falls_back():
    arch = build_architecture_summary({"door_anchor_count": 1, "window_anchor_count": 0})
    pkg = compile_prompt_package(goal(), architecture_summary=arch, llm_client=BadGeometryClient(), mode="llm_with_rule_fallback")
    assert pkg["llm_prompt_compiler_report"]["fallback_used"] is True
    assert "center_m" not in pkg["compiled_text_prompt"]
    assert "bbox" not in pkg["compiled_text_prompt"]
