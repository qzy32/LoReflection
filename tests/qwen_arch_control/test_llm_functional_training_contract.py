
from pathlib import Path


def test_llm_functional_training_scripts_use_context_image_and_forbid_inpaint():
    paths=[Path('scripts/qwen_arch_control/run_p1_small_metric_v2_train.sh'), Path('scripts/qwen_arch_control/run_p1_small_metric_v2_llm_functional_train.sh'), Path('scripts/qwen_arch_control/run_p1_small_metric_v2_mixed_llm_train.sh')]
    text='\n'.join(p.read_text() for p in paths if p.exists())
    assert '--data_file_keys "image,context_image"' in text
    assert '--extra_inputs "context_image"' in text
    assert 'Qwen-Image-In-Context-Control-Union' in text
    for bad in ['blockwise_controlnet_image','blockwise_controlnet_inpaint_mask','control_mask','I_bad','I_target','Qwen-Image-Blockwise-ControlNet-Inpaint','semantic_repair4','RepairPlan','mask_spec']:
        assert bad not in text
