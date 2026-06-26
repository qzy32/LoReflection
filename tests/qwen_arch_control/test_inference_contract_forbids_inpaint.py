from pathlib import Path


def test_inference_scripts_do_not_use_legacy_inpaint_terms():
    paths = [
        Path("scripts/qwen_arch_control/run_p0_sanity_infer.sh"),
        Path("scripts/qwen_arch_control/infer_qwen_arch_incontext.py"),
    ]
    forbidden_parts = [
        ("blockwise_", "controlnet_image"),
        ("blockwise_", "controlnet_inpaint_mask"),
        ("control_", "mask"),
        ("I_", "bad"),
        ("I_", "target"),
        ("Qwen-Image-", "Blockwise-ControlNet-", "Inpaint"),
        ("semantic_", "repair4"),
        ("Repair", "Plan"),
        ("mask_", "spec"),
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for parts in forbidden_parts:
            assert "".join(parts) not in text, f"{path} contains forbidden legacy term {''.join(parts)}"


def test_inference_script_uses_arch_incontext_terms():
    text = Path("scripts/qwen_arch_control/infer_qwen_arch_incontext.py").read_text(encoding="utf-8")
    assert "context_image" in text
    assert "Context_Control." in text
    assert "Qwen-Image-In-Context-Control-Union" in text
    assert "pipe.load_lora" in text
