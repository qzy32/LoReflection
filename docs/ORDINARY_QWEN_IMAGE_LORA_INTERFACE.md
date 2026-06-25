# Ordinary Qwen-Image LoRA Interface

```json
{
  "training_entry": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py",
  "inference_entry": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_inference/Qwen-Image-SLDN-Room.py",
  "metadata_fields": [
    "image",
    "prompt"
  ],
  "image_condition_support": "train.py supports context_image via special_operator_map, but only if extra_inputs includes context_image and metadata contains context_image; current overfit32 ordinary run used data_file_keys=image and no image condition.",
  "text_only_support": true,
  "lora_base_model": "dit",
  "lora_target_modules": "to_q,to_k,to_v,to_out.0,add_q_proj,add_k_proj,add_v_proj,to_add_out (from previous successful overfit32 command)",
  "resolution": "512x512 in current experiments",
  "checkpoint_format": "safetensors LoRA",
  "validation_command": "QwenImagePipeline.from_pretrained(...); pipe.load_lora(pipe.dit, checkpoint); pipe(prompt=..., height=512,width=512)",
  "source_files": [
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_inference/Qwen-Image-SLDN-Room.py"
  ]
}
```
