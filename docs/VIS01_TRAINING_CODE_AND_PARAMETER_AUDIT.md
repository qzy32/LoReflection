# VIS-01 Training Code and Parameter Audit

## Main Training Map

- `diffusion/train_diffsynth_qwen_inpaint_lora.sh`: local/general Qwen-DiffSynth LoRA training wrapper.
- `scripts/c14_3_train_remove_20.sh`, `scripts/c14_3_train_replace_20.sh`, `scripts/c14_3_train_translate_20.sh`, `scripts/c14_3_train_add_20.sh`, `scripts/c14_3_train_mixed_80.sh`: local stubs that call server-side generated scripts.
- `scripts/c14_4_wait_and_run_palette_fixed_clean_training.sh`: C14.4 fixed-step runner.
- Remote train entry: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`.

## Metadata Contract

`image` = I_target, `blockwise_controlnet_image` = I_bad, `blockwise_controlnet_inpaint_mask` = control_mask, `prompt` = correction_prompt.

Server metadata paths: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v2_palette_fixed/metadata_add.csv`, `metadata_remove.csv`, `metadata_translate.csv`, `metadata_replace.csv`, and `metadata_mixed_80.csv`.

## Parameters Actually Used

```json
{
  "dataset_base_path": "/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v2_palette_fixed",
  "base_model": "Qwen/Qwen-Image transformer/text_encoder/vae from DiffSynth model pool",
  "controlnet": "DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint:model.safetensors",
  "batch_size": 1,
  "gradient_accumulation": 1,
  "effective_batch": 1,
  "learning_rate": "1e-4",
  "optimizer": "not explicitly set in C14.4 wrapper; DiffSynth runner default",
  "scheduler": "constant (DiffSynth parser default unless overridden)",
  "lora_rank": 32,
  "lora_alpha": "not explicitly set; add_lora_to_model defaults alpha=rank",
  "lora_dropout": "not explicitly set; PEFT default",
  "precision": "torch.bfloat16 pipeline load",
  "max_pixels": 262144,
  "seed": 4411,
  "gradient_checkpointing": "enabled",
  "num_workers": 0,
  "save_interval": 100,
  "eval_interval": "training validation disabled; external infer-action eval after step100 and step300",
  "extra_inputs": "blockwise_controlnet_image,blockwise_controlnet_inpaint_mask",
  "single_action_fixedsteps": "DATASET_REPEAT=1, NUM_EPOCHS=15, 20 rows -> 300 epoch-end steps",
  "mixed_fixedsteps": "DATASET_REPEAT=1, NUM_EPOCHS=4, 80 rows -> step-300 checkpoint during 320-step epoch end"
}
```

## Checkpoints

```json
{
  "REMOVE": [
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/REMOVE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-100.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/REMOVE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-200.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/REMOVE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-300.safetensors"
  ],
  "REPLACE": [
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/REPLACE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-100.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/REPLACE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-200.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/REPLACE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-300.safetensors"
  ],
  "TRANSLATE": [
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/TRANSLATE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-100.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/TRANSLATE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-200.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/TRANSLATE_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-300.safetensors"
  ],
  "ADD": [
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/ADD_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-100.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/ADD_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-200.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/ADD_20/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-300.safetensors"
  ],
  "MIXED": [
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/MIXED_80/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-100.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/MIXED_80/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-200.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/MIXED_80/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-300.safetensors",
    "/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_palette_fixed_v1/MIXED_80/c14_4_fixedsteps_gpu0_rank32_300steps/run/step-320.safetensors"
  ]
}
```

## Unknown or Default Parameters

Optimizer, LoRA dropout, and some accelerator details are not explicitly set by the C14.4 wrapper; they use DiffSynth/PEFT defaults unless the remote runner sets them internally.
