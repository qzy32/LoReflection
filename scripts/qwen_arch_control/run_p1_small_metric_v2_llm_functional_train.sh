#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata_llm_functional.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional}"
export INIT_LORA="${INIT_LORA:-$ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2/train/run/epoch-2.safetensors}"
export P1_DATASET_REPEAT="${P1_DATASET_REPEAT:-10}"
export P1_NUM_EPOCHS="${P1_NUM_EPOCHS:-3}"
export P1_MAX_PIXELS="${P1_MAX_PIXELS:-65536}"
export P1_LR="${P1_LR:-1e-4}"
export P1_LORA_RANK="${P1_LORA_RANK:-64}"
bash "$ROOT/scripts/qwen_arch_control/run_p1_small_metric_v2_train.sh"
