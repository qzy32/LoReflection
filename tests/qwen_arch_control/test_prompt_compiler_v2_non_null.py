import json

from loreflection.qwen_arch_control.prompt_labels.prompt_compiler_v2 import compile_prompt_package_v2


def test_prompt_compiler_v2_controls_are_non_null_and_traceable(tmp_path):
    palette = tmp_path / "c2rgb.json"
    palette.write_text(json.dumps({"coffee_table": [78, 224, 72], "dining_table": [224, 103, 72]}), encoding="utf-8")
    package = compile_prompt_package_v2(
        user_intent_prompt="Context_Control. Place 1 coffee_table and 1 dining_table in the livingroom.",
        goal_lostate={"required_counts": {"coffee_table": 1, "dining_table": 1}},
        prompt_package={
            "schema_version": "test",
            "geometry_verified_constraints": [],
            "dropped_constraints": [{"subject": "coffee_table", "predicate": "near", "object": "dining_table"}],
        },
        c2rgb_path=palette,
        source_prompt_package="meta/source_prompt_package.json",
        goal_lostate_ref="meta/goal.json",
    )
    assert package["user_intent_prompt"]
    assert package["architecture_control_prompt"]
    assert package["palette_control_prompt"]
    assert package["compiled_prompt"] != package["user_intent_prompt"]
    assert "Architecture_Control." in package["compiled_prompt"]
    assert "Palette_Control." in package["compiled_prompt"]
    assert package["dropped_constraints"][0]["subject"] == "coffee_table"
    assert package["goal_lostate_ref"] == "meta/goal.json"
