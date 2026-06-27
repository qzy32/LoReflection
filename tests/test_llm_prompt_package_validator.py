import pytest

from loreflection.goal.prompt_compiler import compile_prompt_package
from loreflection.goal.llm_functional_prompt_compiler import build_architecture_summary
from loreflection.goal.prompt_package_validator import (
    ERROR_GEOMETRY_LEAKAGE,
    ERROR_INVALID_ARCHITECTURE_CLAIM,
    ERROR_LAYOUT_JSON,
    ERROR_UNKNOWN_CATEGORY,
    PromptCompilerError,
)


def goal():
    return {
        "room_type": "bedroom",
        "required_counts": {"double_bed": 1},
        "furniture_slots": [{"slot_id": "goal:double_bed", "category": "double_bed", "count": 1, "required": True}],
        "goal_constraints": [{"constraint_id": "inside_room", "constraint_kind": "global", "necessity": "required"}],
    }


def assert_error(client, code):
    with pytest.raises(PromptCompilerError) as exc:
        compile_prompt_package(goal(), architecture_summary=build_architecture_summary({}), registry={"colors": {"double_bed": [72, 224, 199]}}, llm_client=client)
    assert exc.value.code == code


class GeometryLeakClient:
    def generate_json(self, *_):
        return {"compiled_text_prompt": "Create a bedroom with double_bed at center_m and bbox.", "used_slot_ids": ["goal:double_bed"], "used_constraint_ids": [], "omitted_constraint_ids": ["inside_room"], "architecture_claims": ["room_floor_boundary"], "notes": []}


class UnknownCategoryClient:
    def generate_json(self, *_):
        return {"compiled_text_prompt": "Create a top_down layout with one fake_sofa and one double_bed.", "used_slot_ids": ["goal:double_bed"], "used_constraint_ids": [], "omitted_constraint_ids": ["inside_room"], "architecture_claims": ["room_floor_boundary"], "notes": []}


class InvalidClaimClient:
    def generate_json(self, *_):
        return {"compiled_text_prompt": "Create a top-down fixed-palette semantic bedroom layout with one double_bed.", "used_slot_ids": ["goal:double_bed"], "used_constraint_ids": [], "omitted_constraint_ids": ["inside_room"], "architecture_claims": ["room_floor_boundary", "visible_wall"], "notes": []}


class LayoutJsonClient:
    def generate_json(self, *_):
        return {"compiled_text_prompt": "Create a layout_json for one double_bed.", "used_slot_ids": ["goal:double_bed"], "used_constraint_ids": [], "omitted_constraint_ids": ["inside_room"], "architecture_claims": ["room_floor_boundary"], "notes": []}


def test_geometry_leakage_fails():
    assert_error(GeometryLeakClient(), ERROR_GEOMETRY_LEAKAGE)


def test_unknown_category_fails():
    assert_error(UnknownCategoryClient(), ERROR_UNKNOWN_CATEGORY)


def test_invalid_architecture_claim_fails():
    assert_error(InvalidClaimClient(), ERROR_INVALID_ARCHITECTURE_CLAIM)


def test_layout_json_fails():
    assert_error(LayoutJsonClient(), ERROR_LAYOUT_JSON)
