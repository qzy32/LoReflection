#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"

export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_full_metric_v2_full_semantic_compiled_main}"

/home/chengjiajia/anaconda3/bin/python scripts/qwen_arch_control/quantize_qwen_output_palette.py \
  --input-dir "$OUT/infer" \
  --output-dir "$OUT/quantized" \
  --report "$OUT/eval/palette_quantization_report.json"

/home/chengjiajia/anaconda3/bin/python scripts/qwen_arch_control/evaluate_full_semantic_outputs.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --output "$OUT/eval/full_semantic_eval_report_raw.json"

/home/chengjiajia/anaconda3/bin/python scripts/qwen_arch_control/evaluate_full_semantic_outputs.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --output "$OUT/eval/full_semantic_eval_report_copyback.json" \
  --sanitized
