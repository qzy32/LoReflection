# Clean 512 Qwen training status

Dataset: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_raw3dfront_clean_512_oob050`
Metadata: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_raw3dfront_clean_512_oob050/metadata.csv`
Training run: `qwen_arch_raw3dfront_clean512_oob050_rank64_fp8exact_cuda_20260629_210803`
Training log: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/logs/qwen_arch_raw3dfront_clean512_oob050_rank64_fp8exact_cuda_20260629_210803.log`
Output: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/models/train/qwen_arch_raw3dfront_clean512_oob050_rank64_fp8exact_cuda_20260629_210803`

Notes:
- Full clean dataset gate passed.
- Training is launched in tmux on GPU3.
- FP8/offload model arguments must use exact `model_id_with_origin_paths` strings; model names like `qwen_image_dit` do not match DiffSynth's parser.
- Rank64 LoRA checkpoint was loaded successfully.
- Metrics JSONL contains train step/loss entries.
