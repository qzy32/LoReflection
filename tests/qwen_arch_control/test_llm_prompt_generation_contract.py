from scripts.qwen_arch_control.generate_llm_prompt_variants import build_messages, extract_json_object, normalize_prompt_object, scrub_forbidden


def test_llm_prompt_json_parse_and_normalize():
    obj = extract_json_object('```json\n{"prompt_llm_short":"short","prompt_llm_functional":"Context_Control. good","prompt_llm_user_like":"user"}\n```')
    prompts = normalize_prompt_object(obj)
    assert all(value.startswith("Context_Control.") for value in prompts.values())


def test_llm_request_scrubs_geometry():
    request = {"user": {"scene_facts": {"center_m": [1, 2], "furniture_counts": {"desk": 1}}, "goal_lostate_rich_without_geometry": {"bbox_px": [1, 2, 3, 4]}}}
    messages = build_messages(request)
    text = str(messages)
    assert "center_m" not in text
    assert "bbox_px" not in text
    assert "desk" in text
