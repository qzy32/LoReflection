from scripts.qwen_arch_control.build_full_semantic_compiled_dataset import build_user_intent


def test_full_semantic_compiled_user_intent_uses_only_verified_relations():
    goal = {
        "room_type": "livingroom",
        "required_counts": {"coffee_table": 1, "dining_table": 1},
        "pairwise_constraints": [],
        "dropped_pairwise_constraints": [
            {"subject": "coffee_table", "predicate": "near", "object": "dining_table", "prompt_allowed": False}
        ],
    }
    prompt = build_user_intent(goal)
    assert prompt.startswith("Context_Control.")
    assert "coffee_table" in prompt
    assert "dining_table" in prompt
    assert "near dining_table" not in prompt
