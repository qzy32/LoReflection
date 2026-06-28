#!/usr/bin/env bash
set -euo pipefail
cd /wuqingyaoa800/qiuziyan/LoReflection_arch_p0
export CUDA_VISIBLE_DEVICES=0
export DATASET_ROOT="/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled"
export OUT="/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/models/train/loreflection_qwen_arch_incontext_lora_llm_applied_20260628_035630"
export DIFFSYNTH_ROOT=/wuqingyaoa800/qiuziyan/DiffSynth-Studio
export PYTHON_BIN=/wuqingyaoa800/qiuziyan/envs/diffsynth-qwen/bin/python
export ACCELERATE_BIN=/wuqingyaoa800/qiuziyan/envs/diffsynth-qwen/bin/accelerate
export DIFFSYNTH_MODEL_BASE_PATH=/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models
export DIFFSYNTH_SKIP_DOWNLOAD=true
export FULL_DATASET_REPEAT=20
export FULL_NUM_EPOCHS=5
export FULL_MAX_PIXELS=65536
export FULL_LR=1e-4
export FULL_LORA_RANK=64
bash scripts/qwen_arch_control/run_full_metric_v2_full_semantic_compiled_main_train.sh
