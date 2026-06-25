# Blockwise Inpaint LoRA Interface

```json
{
  "training_entry_lora": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/lora/Qwen-Image-Blockwise-ControlNet-Inpaint.sh",
  "training_entry_full": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/full/Qwen-Image-Blockwise-ControlNet-Inpaint.sh",
  "inference_entry": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_inference/Qwen-Image-Blockwise-ControlNet-Inpaint.py",
  "metadata_fields_expected": [
    "image",
    "blockwise_controlnet_image",
    "blockwise_controlnet_inpaint_mask",
    "prompt"
  ],
  "extra_inputs": [
    "blockwise_controlnet_image",
    "blockwise_controlnet_inpaint_mask"
  ],
  "mask_convention": "to be empirically confirmed from inference script/pipeline; likely PIL mask passed as inpaint mask where white/high values select repaint region, but report records source lines for verification.",
  "checkpoint_format": "safetensors LoRA",
  "source_files": [
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/lora/Qwen-Image-Blockwise-ControlNet-Inpaint.sh",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/full/Qwen-Image-Blockwise-ControlNet-Inpaint.sh",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_inference/Qwen-Image-Blockwise-ControlNet-Inpaint.py",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_inference_low_vram/Qwen-Image-Blockwise-ControlNet-Inpaint.py",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/diffsynth/pipelines/qwen_image.py"
  ],
  "relevant_source_report": "reports/c8g_interface_source_excerpt.json"
}
```

See `reports/c8g_interface_source_excerpt.json` for source-line evidence.
