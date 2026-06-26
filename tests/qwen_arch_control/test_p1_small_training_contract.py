from pathlib import Path


def test_p1_small_train_script_uses_context_and_not_legacy_inpaint():
    path = Path('scripts/qwen_arch_control/run_p1_small_train.sh')
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    assert '--data_file_keys "image,context_image"' in text
    assert '--extra_inputs "context_image"' in text
    assert 'Qwen-Image-In-Context-Control-Union' in text
    forbidden = [
        'blockwise_controlnet_image',
        'blockwise_controlnet_inpaint_mask',
        'control_mask',
        'I_bad',
        'I_target',
        'Qwen-Image-Blockwise-ControlNet-Inpaint',
        'semantic_repair4',
    ]
    for term in forbidden:
        assert term not in text
