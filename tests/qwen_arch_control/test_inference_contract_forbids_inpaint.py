from pathlib import Path


def test_inference_scripts_use_current_arch_incontext_contract():
    shell_text = Path("scripts/qwen_arch_control/run_p0_sanity_infer.sh").read_text(encoding="utf-8")
    assert "infer_qwen_arch_incontext.py" in shell_text

    infer_text = Path("scripts/qwen_arch_control/infer_qwen_arch_incontext.py").read_text(encoding="utf-8")
    assert "context_image" in infer_text
    assert "Qwen-Image-In-Context-Control-Union" in infer_text


def test_inference_script_uses_arch_incontext_terms():
    text = Path("scripts/qwen_arch_control/infer_qwen_arch_incontext.py").read_text(encoding="utf-8")
    assert "context_image" in text
    assert "Context_Control." in text
    assert "Qwen-Image-In-Context-Control-Union" in text
    assert "pipe.load_lora" in text
