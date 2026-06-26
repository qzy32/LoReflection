#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=${REPO_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0}
DATASET_ROOT=${DATASET_ROOT:-$REPO_ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm}
METADATA=${METADATA:-$DATASET_ROOT/metadata_llm_functional_compiled_palette.csv}
OUT=${OUT:-$REPO_ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional_compiled_palette}

python "$REPO_ROOT/scripts/qwen_arch_control/quantize_qwen_output_palette.py" \
  --input-dir "$OUT/infer" \
  --output-dir "$OUT/quantized" \
  --report "$OUT/eval/palette_quantization_report.json"

python "$REPO_ROOT/scripts/qwen_arch_control/evaluate_p0_sanity_outputs.py" \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --train-log "$OUT/logs/train.log" \
  --script "$REPO_ROOT/scripts/qwen_arch_control/run_p1_small_metric_v2_llm_functional_compiled_palette_train.sh" \
  --script "$REPO_ROOT/scripts/qwen_arch_control/run_p1_small_metric_v2_llm_functional_compiled_palette_infer.sh" \
  --checkpoint-used "$OUT/train/run/epoch-2.safetensors" \
  --phase-label p1
