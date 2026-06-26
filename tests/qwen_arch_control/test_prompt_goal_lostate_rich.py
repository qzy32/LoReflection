import pytest

from loreflection.qwen_arch_control.prompt_labels.goal_constraint_extractor import assert_no_geometry, build_rich_goal_lostate


def test_rich_goal_lostate_has_no_geometry():
    facts = {"sample_id": "s1", "room_type": "bedroom", "furniture_counts": {"double_bed": 1}, "relation_facts": [], "global_constraints": ["inside_room"]}
    goal = build_rich_goal_lostate(facts, "meta/s1_architecture.json")
    assert goal["required_counts"] == {"double_bed": 1}
    assert_no_geometry(goal)


def test_geometry_terms_rejected():
    with pytest.raises(ValueError):
        assert_no_geometry({"center_m": [0, 0]})
