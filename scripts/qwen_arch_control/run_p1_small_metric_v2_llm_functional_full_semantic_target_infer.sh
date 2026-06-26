#!/usr/bin/env bash
set -euo pipefail

# Draft wrapper for the full-semantic target ablation.
REPO_ROOT=${REPO_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0}
DATASET_ROOT=${DATASET_ROOT:-$REPO_ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_full_semantic_target}
METADATA=${METADATA:-$DATASET_ROOT/metadata_llm_functional_full_semantic_target.csv}
OUT=${OUT:-$REPO_ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional_full_semantic_target}
P1_FULL_SEMANTIC_LORA=${P1_FULL_SEMANTIC_LORA:-$OUT/train/run/epoch-2.safetensors}
SAMPLES=${SAMPLES:-20}
HEIGHT=${HEIGHT:-256}
WIDTH=${WIDTH:-256}
STEPS=${STEPS:-20}
SEED=${SEED:-5521}

python "$REPO_ROOT/scripts/qwen_arch_control/infer_qwen_arch_incontext.py" \
  --dataset-root "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --lora "$P1_FULL_SEMANTIC_LORA" \
  --out "$OUT" \
  --num-samples "$SAMPLES" \
  --height "$HEIGHT" \
  --width "$WIDTH" \
  --steps "$STEPS" \
  --seed "$SEED"
