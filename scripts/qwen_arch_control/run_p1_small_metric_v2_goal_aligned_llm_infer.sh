#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_goal_aligned_llm_prompts}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata_goal_aligned_relation_rich.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_goal_aligned_llm}"
export P1_METRIC_V2_LORA="${P1_METRIC_V2_LORA:-$OUT/train/run/epoch-2.safetensors}"
export P1_METRIC_V2_INFER_SAMPLES="${P1_METRIC_V2_INFER_SAMPLES:-20}"
export P1_METRIC_V2_INFER_HEIGHT="${P1_METRIC_V2_INFER_HEIGHT:-256}"
export P1_METRIC_V2_INFER_WIDTH="${P1_METRIC_V2_INFER_WIDTH:-256}"
export P1_METRIC_V2_INFER_STEPS="${P1_METRIC_V2_INFER_STEPS:-20}"
export P1_METRIC_V2_SEED="${P1_METRIC_V2_SEED:-7711}"
bash "$ROOT/scripts/qwen_arch_control/run_p1_small_metric_v2_infer.sh"
