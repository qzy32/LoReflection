from pathlib import Path


def test_architecture_scale_contract_states_qwen_does_not_generate_architecture():
    text = Path("reports/architecture_condition_scale/ARCHITECTURE_SCALE_CONTRACT.md").read_text(encoding="utf-8")
    assert "Qwen does not generate architecture" in text
    assert "Qwen generates furniture semantic image content only" in text
    assert "raw 3D-FRONT scene JSON is the source of truth" in text
    assert "metric_v2" in text
