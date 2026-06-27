import pytest

from loreflection.goal.prompt_compiler import compile_prompt_package
from loreflection.goal.llm_functional_prompt_compiler import build_architecture_summary
from loreflection.goal.prompt_package_validator import ERROR_CLIENT_MISSING, PromptCompilerError


def goal():
    return {
        "room_type": "bedroom",
        "required_counts": {"double_bed": 1, "wardrobe": 1},
        "furniture_slots": [
            {"slot_id": "goal:double_bed", "category": "double_bed", "count": 1, "required": True, "role": "sleeping"},
            {"slot_id": "goal:wardrobe", "category": "wardrobe", "count": 1, "required": True, "role": "storage"},
        ],
        "goal_constraints": [
            {"constraint_id": "inside_room", "constraint_kind": "global", "necessity": "required", "prompt_hint": "Keep furniture inside the room floor region."},
            {"constraint_id": "door_clearance_free", "constraint_kind": "region", "necessity": "required", "prompt_hint": "Keep the visible door area clear."},
        ],
    }


class GoodClient:
    def generate_json(self, system_prompt, user_payload):
        return {
            "compiled_text_prompt": "Create a top-down fixed-palette semantic bedroom layout with one double_bed and one wardrobe. Use the room floor boundary and visible door to keep the entrance clear.",
            "used_slot_ids": ["goal:double_bed", "goal:wardrobe"],
            "used_constraint_ids": ["inside_room", "door_clearance_free"],
            "omitted_constraint_ids": [],
            "architecture_claims": ["room_floor_boundary", "visible_door"],
            "notes": [],
        }


def test_llm_functional_prompt_compiler_with_mock_client():
    arch = build_architecture_summary({"door_anchor_count": 1})
    pkg = compile_prompt_package(goal(), architecture_summary=arch, registry={"colors": {"double_bed": [72, 224, 199], "wardrobe": [72, 224, 128]}}, llm_client=GoodClient())
    assert pkg["prompt_compiler"] == "llm_functional"
    assert pkg["validation_report"]["status"] == "pass"
    assert "double_bed=(72,224,199)" in pkg["compiled_text_prompt"]
    assert "wardrobe=(72,224,128)" in pkg["compiled_text_prompt"]


def test_missing_llm_client_fails_without_fallback():
    with pytest.raises(PromptCompilerError) as exc:
        compile_prompt_package(goal(), architecture_summary=build_architecture_summary({}), registry={"colors": {"double_bed": [1, 2, 3]}})
    assert exc.value.code == ERROR_CLIENT_MISSING
