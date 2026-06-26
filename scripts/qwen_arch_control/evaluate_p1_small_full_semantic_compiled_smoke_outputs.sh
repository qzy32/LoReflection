#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_full_semantic_compiled}"
export METADATA="${METADATA:-$ROOT/outputs/qwen_arch_incontext_p1_small_full_semantic_compiled_smoke_strong/subsets/metadata_smoke_32.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_p1_small_full_semantic_compiled_smoke_strong}"
PYTHON_BIN="${PYTHON_BIN:-/wuqingyaoa800/qiuziyan/envs/qwen35-serve/bin/python}"
mkdir -p "$OUT/eval" "$OUT/quantized"
"$PYTHON_BIN" scripts/qwen_arch_control/quantize_qwen_output_palette.py \
  --input-dir "$OUT/infer" \
  --output-dir "$OUT/quantized" \
  --report "$OUT/eval/palette_quantization_report.json"
"$PYTHON_BIN" scripts/qwen_arch_control/evaluate_full_semantic_outputs.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --output "$OUT/eval/full_semantic_smoke_eval_report.json"
"$PYTHON_BIN" scripts/qwen_arch_control/evaluate_full_semantic_outputs.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --output "$OUT/eval/full_semantic_smoke_eval_sanitized_report.json" \
  --sanitized
