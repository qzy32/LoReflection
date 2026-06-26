# P0 Sanity Training Summary

## Scope

This run is a P0 sanity overfit test for Qwen-Image Architecture In-Context Control. It is not full training and not a paper-scale experiment.

## Dataset

- Dataset package: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_real_p0`
- Metadata: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_real_p0/metadata.csv`
- Tiny subset: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/subsets/p0_tiny_8.csv`
- P0 50 subset: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/subsets/p0_50.csv`
- Dataset source: real 3D-FRONT P0 package, not procedural contract data.

## Training Status

- Tiny training: passed; checkpoint count = 1
- P0_50 training: passed; checkpoint count = 3
- DiffSynth root: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio`
- Python: `/home/chengjiajia/anaconda3/envs/DiffSynth-Studio/bin/python`
- GPU: `2`
- Train command logs: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/logs/train_tiny_command.txt`, `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/logs/train_p0_50_command.txt`
- Train logs: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/logs/train_tiny.log`, `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/logs/train_p0_50.log`

## Checkpoints

Tiny:
- `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/train_tiny/run/epoch-0.safetensors`

P0_50:
- `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/train_p0_50/run/epoch-0.safetensors`
- `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/train_p0_50/run/epoch-1.safetensors`
- `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/train_p0_50/run/epoch-2.safetensors`

## Contract

- Uses `--data_file_keys image,context_image`: True
- Uses `--extra_inputs context_image`: True
- Uses In-Context-Control-Union LoRA: True
- Forbidden old inpaint fields present: False
- Dataset is real 3D-FRONT: True

## Inference And Evaluation

- Inference status: TODO wrapper written, no fabricated outputs.
- Inference TODO: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/infer/INFER_TODO.md`
- Quantized output dir: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/quantized`
- Palette quantization report: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/eval/palette_quantization_report.json`
- P0 sanity eval report: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/eval/p0_sanity_eval_report.json`
- Number of train samples: 50
- Number of infer samples: 0
- Overfit success: None

## Next Step

Training ingestion succeeded for both tiny and P0_50. The remaining blocker is a verified DiffSynth Architecture In-Context inference wrapper for prompt + context_image + trained LoRA. After that wrapper exists, run 10-sample inference, quantize to the frozen semantic palette, and compute visual overfit metrics before moving to P1 200-1000 samples.


## Pytest

- Command: `/home/chengjiajia/anaconda3/bin/python -m pytest tests/qwen_arch_control`
- Result: `9 passed in 0.52s`
- Log: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/reports/p0_sanity/pytest_qwen_arch_control_after_train.log`
