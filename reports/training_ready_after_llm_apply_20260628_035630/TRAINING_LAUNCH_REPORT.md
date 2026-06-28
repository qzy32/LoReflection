# Training Launch Report

- dataset_root: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled`
- metadata_path: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled/metadata.csv`
- metadata_rows: `4879`
- prompt_compiler: `llm_functional`
- fallback: `false 4879/4879`
- active RGB palette entries: `4879/4879`
- opening_policy: `semlayoutdiff_room_children_only`
- full_gate_audit_status: `pass`
- train_pid: `2837788`
- train_log: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/reports/training_ready_after_llm_apply_20260628_035630/train.log`
- train_output_path: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/models/train/loreflection_qwen_arch_incontext_lora_llm_applied_20260628_035630`
- cuda_visible_devices: `0`

## Status Check

- status_checked_at: 2026-06-28 04:19:06
- ps_status:

```text
UID          PID    PPID  C STIME TTY          TIME CMD
qiuziyan 2837788       1  0 04:16 ?        00:00:00 bash reports/training_ready_after_llm_apply_20260628_035630/training_command.sh
```

- train_log_tail_file: `reports/training_ready_after_llm_apply_20260628_035630/train_log_tail_20260628_041906.txt`

## Current train.log tail

```text
]
Loaded model: {
    "model_name": "qwen_image_dit",
    "model_class": "diffsynth.models.qwen_image_dit.QwenImageDiT",
    "extra_kwargs": null
}
Loading models from: [
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00003-of-00004.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00002-of-00004.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00004-of-00004.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00001-of-00004.safetensors"
]
Loaded model: {
    "model_name": "qwen_image_text_encoder",
    "model_class": "diffsynth.models.qwen_image_text_encoder.QwenImageTextEncoder",
    "extra_kwargs": null
}
Loading models from: "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/vae/diffusion_pytorch_model.safetensors"
Loaded model: {
    "model_name": "qwen_image_vae",
    "model_class": "diffsynth.models.qwen_image_vae.QwenImageVAE",
    "extra_kwargs": null
}
Using qwen_image_text_encoder from [
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00003-of-00004.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00002-of-00004.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00004-of-00004.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/text_encoder/model-00001-of-00004.safetensors"
].
Using qwen_image_dit from [
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00006-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00009-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00008-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00002-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00001-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00004-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00007-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00005-of-00009.safetensors",
    "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/transformer/diffusion_pytorch_model-00003-of-00009.safetensors"
].
Using qwen_image_vae from "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models/Qwen/Qwen-Image/vae/diffusion_pytorch_model.safetensors".
No qwen_image_blockwise_controlnet models available. This is not an error.
No siglip2_image_encoder models available. This is not an error.
No dinov3_image_encoder models available. This is not an error.
No qwen_image_image2lora_style models available. This is not an error.
No qwen_image_image2lora_coarse models available. This is not an error.
No qwen_image_image2lora_fine models available. This is not an error.
LoRA checkpoint loaded: /wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small_metric_v2/train/run/epoch-2.safetensors, total 1440 keys
Metrics JSONL logging enabled: /wuqingyaoa800/qiuziyan/LoReflection_arch_p0/models/train/loreflection_qwen_arch_incontext_lora_llm_applied_20260628_035630/train/run/train_metrics.jsonl
epoch 0:   0%|          | 0/97580 [00:00<?, ?it/s]epoch 0:   0%|          | 1/97580 [00:05<152:04:29,  5.61s/it]epoch 0:   0%|          | 2/97580 [00:06<79:28:30,  2.93s/it] epoch 0:   0%|          | 3/97580 [00:07<54:45:48,  2.02s/it]epoch 0:   0%|          | 4/97580 [00:08<43:10:02,  1.59s/it]epoch 0:   0%|          | 5/97580 [00:09<36:34:35,  1.35s/it]epoch 0:   0%|          | 6/97580 [00:10<32:43:22,  1.21s/it]epoch 0:   0%|          | 7/97580 [00:11<31:25:00,  1.16s/it]epoch 0:   0%|          | 8/97580 [00:12<29:30:58,  1.09s/it]epoch 0:   0%|          | 9/97580 [00:13<28:06:36,  1.04s/it]epoch 0:   0%|          | 10/97580 [00:14<27:19:21,  1.01s/it]epoch 0:   0%|          | 11/97580 [00:15<26:33:22,  1.02it/s]epoch 0:   0%|          | 12/97580 [00:16<27:24:37,  1.01s/it]epoch 0:   0%|          | 13/97580 [00:17<26:40:42,  1.02it/s]epoch 0:   0%|          | 14/97580 [00:18<26:12:35,  1.03it/s]epoch 0:   0%|          | 15/97580 [00:19<25:53:03,  1.05it/s]epoch 0:   0%|          | 16/97580 [00:19<25:43:31,  1.05it/s]epoch 0:   0%|          | 17/97580 [00:21<26:35:40,  1.02it/s]epoch 0:   0%|          | 18/97580 [00:21<26:09:30,  1.04it/s]epoch 0:   0%|          | 19/97580 [00:22<25:44:03,  1.05it/s]epoch 0:   0%|          | 20/97580 [00:23<25:36:02,  1.06it/s]epoch 0:   0%|          | 21/97580 [00:24<25:31:26,  1.06it/s]epoch 0:   0%|          | 22/97580 [00:25<26:40:21,  1.02it/s]epoch 0:   0%|          | 23/97580 [00:26<26:12:45,  1.03it/s]epoch 0:   0%|          | 24/97580 [00:27<25:55:37,  1.05it/s]epoch 0:   0%|          | 25/97580 [00:28<25:39:43,  1.06it/s]epoch 0:   0%|          | 26/97580 [00:29<26:57:17,  1.01it/s]epoch 0:   0%|          | 27/97580 [00:30<26:22:16,  1.03it/s]epoch 0:   0%|          | 28/97580 [00:31<25:56:19,  1.04it/s]epoch 0:   0%|          | 29/97580 [00:32<25:40:02,  1.06it/s]epoch 0:   0%|          | 30/97580 [00:33<25:31:14,  1.06it/s]epoch 0:   0%|          | 31/97580 [00:34<26:40:48,  1.02it/s]epoch 0:   0%|          | 32/97580 [00:35<26:18:27,  1.03it/s]epoch 0:   0%|          | 33/97580 [00:36<25:57:51,  1.04it/s]epoch 0:   0%|          | 34/97580 [00:37<25:39:32,  1.06it/s]epoch 0:   0%|          | 35/97580 [00:38<25:29:03,  1.06it/s]epoch 0:   0%|          | 36/97580 [00:39<26:36:15,  1.02it/s]epoch 0:   0%|          | 37/97580 [00:40<26:17:27,  1.03it/s]epoch 0:   0%|          | 38/97580 [00:41<25:52:41,  1.05it/s]epoch 0:   0%|          | 39/97580 [00:42<25:34:31,  1.06it/s]epoch 0:   0%|          | 40/97580 [00:42<25:20:32,  1.07it/s]epoch 0:   0%|          | 41/97580 [00:44<26:31:32,  1.02it/s]epoch 0:   0%|          | 42/97580 [00:44<26:00:37,  1.04it/s]epoch 0:   0%|          | 43/97580 [00:45<25:42:13,  1.05it/s]epoch 0:   0%|          | 44/97580 [00:46<25:34:08,  1.06it/s]epoch 0:   0%|          | 45/97580 [00:47<25:31:08,  1.06it/s]epoch 0:   0%|          | 46/97580 [00:48<26:31:38,  1.02it/s]epoch 0:   0%|          | 47/97580 [00:49<26:11:48,  1.03it/s]epoch 0:   0%|          | 48/97580 [00:50<25:52:31,  1.05it/s]epoch 0:   0%|          | 49/97580 [00:51<25:47:13,  1.05it/s]
```

## Latest Status Refresh

- refreshed_at: 2026-06-28T04:30:27+00:00
- train_pid: 2837788
- latest_tail: reports/training_ready_after_llm_apply_20260628_035630/train_log_tail_latest.txt
- status: process observed running after launch; epoch 0 progress continuing in train.log.
