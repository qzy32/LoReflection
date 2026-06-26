#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=${REPO_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0}
DATASET_ROOT=${DATASET_ROOT:-$REPO_ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm}
METADATA=${METADATA:-$DATASET_ROOT/metadata_llm_functional_compiled_palette.csv}
OUT=${OUT:-$REPO_ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional_compiled_palette}
P1_METRIC_V2_LORA=${P1_METRIC_V2_LORA:-$OUT/train/run/epoch-2.safetensors}

bash "$REPO_ROOT/scripts/qwen_arch_control/run_p1_small_metric_v2_infer.sh"
