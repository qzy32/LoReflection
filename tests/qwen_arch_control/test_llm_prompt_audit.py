import json
from pathlib import Path

from loreflection.qwen_arch_control.prompt_labels.audit_llm_prompt_outputs import audit_llm_prompt_outputs


def test_llm_prompt_audit_passes_clean_outputs(tmp_path: Path):
    request = {
        "sample_id": "s1",
        "user": {
            "scene_facts": {"furniture_counts": {"desk": 1}},
            "goal_lostate_rich_without_geometry": {"furniture_slots": [{"category": "desk", "count": 1}]},
        },
    }
    req = tmp_path / "requests.jsonl"
    req.write_text(json.dumps(request) + "\n", encoding="utf-8")
    output = tmp_path / "outputs.jsonl"
    row = {
        "sample_id": "s1",
        "model_path": "/models/qwen",
        "parse_ok": True,
        "prompts": {
            "prompt_llm_short": "Context_Control. Create a room with one desk.",
            "prompt_llm_functional": "Context_Control. Design a room around one desk.",
            "prompt_llm_user_like": "Context_Control. I need one desk in the room.",
        },
    }
    output.write_text(json.dumps(row) + "\n", encoding="utf-8")
    report = audit_llm_prompt_outputs(output, req, expected_count=1)
    assert report["json_parse_success_rate"] == 1.0
    assert report["coordinate_leakage_rate"] == 0.0
    assert report["required_slot_coverage_rate"] == 1.0
