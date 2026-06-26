from pathlib import Path


def test_metric_v2_training_script_uses_context_and_forbids_inpaint():
    text = Path("scripts/qwen_arch_control/run_p1_small_metric_v2_train.sh").read_text(encoding="utf-8")
    assert '--data_file_keys "image,context_image"' in text
    assert '--extra_inputs "context_image"' in text
    assert "Qwen-Image-In-Context-Control-Union" in text
    for term in ["blockwise_controlnet_image", "blockwise_controlnet_inpaint_mask", "control_mask", "I_bad", "I_target", "semantic_repair4"]:
        assert term not in text
