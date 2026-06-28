from pathlib import Path


def test_p1_small_train_script_uses_current_context_contract():
    path = Path('scripts/qwen_arch_control/run_p1_small_train.sh')
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    assert '--data_file_keys "image,context_image"' in text
    assert '--extra_inputs "context_image"' in text
    assert 'Qwen-Image-In-Context-Control-Union' in text
