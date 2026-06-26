from loreflection.qwen_arch_control.prompt_labels.relation_geometry_validator import (
    validate_pairwise_constraints_against_target,
)


def test_near_relation_requires_target_geometry():
    layout = {
        "objects": [
            {"instance_id": "coffee_1", "category": "coffee_table", "center_m": [0.0, 0.0], "size_m": [0.5, 0.5]},
            {"instance_id": "dining_1", "category": "dining_table", "center_m": [4.0, 0.0], "size_m": [1.0, 1.0]},
        ]
    }
    report = validate_pairwise_constraints_against_target(
        [{"subject": "coffee_table", "predicate": "near", "object": "dining_table", "source": "rule"}],
        layout_json=layout,
    )
    assert report["geometry_verified"] == []
    assert report["dropped"][0]["reason"] == "target_geometry_not_near"
    assert report["dropped"][0]["prompt_allowed"] is False


def test_near_relation_passes_when_edge_gap_is_small():
    layout = {
        "objects": [
            {"instance_id": "chair_1", "category": "dining_chair", "center_m": [0.0, 0.0], "size_m": [0.4, 0.4]},
            {"instance_id": "table_1", "category": "dining_table", "center_m": [0.7, 0.0], "size_m": [0.8, 0.8]},
        ]
    }
    report = validate_pairwise_constraints_against_target(
        [{"subject": "dining_chair", "predicate": "near", "object": "dining_table", "source": "rule"}],
        layout_json=layout,
    )
    assert report["geometry_verified"][0]["source"] == "geometry_verified"
    assert report["geometry_verified"][0]["prompt_allowed"] is True
    assert report["dropped"] == []
