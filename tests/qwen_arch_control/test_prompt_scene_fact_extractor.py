from loreflection.qwen_arch_control.prompt_labels.scene_fact_extractor import extract_scene_facts, infer_room_type


def test_scene_fact_extractor_counts_and_infers_room_type():
    layout = {"objects": [{"category": "double_bed"}, {"category": "nightstand"}, {"category": "nightstand"}]}
    arch = {"anchors": [{"anchor_type": "door"}], "metric_transform": {"schema_version": "metric-transform-v1"}}
    facts = extract_scene_facts(layout, arch, "s1")
    assert facts["room_type"] == "bedroom"
    assert facts["furniture_counts"]["nightstand"] == 2
    assert facts["architecture_facts"]["metric_transform_exists"] is True
    assert "door_clearance_free" in facts["global_constraints"]


def test_room_type_rule_livingroom():
    assert infer_room_type({"sofa": 1, "coffee_table": 1}) == ("livingroom", "furniture_rule")
