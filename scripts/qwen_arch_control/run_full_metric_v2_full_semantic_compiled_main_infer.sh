#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"

export DIFFSYNTH_ROOT="${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}"
export PYTHON_BIN="${PYTHON_BIN:-/home/chengjiajia/anaconda3/envs/DiffSynth-Studio/bin/python}"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_full_metric_v2_full_semantic_compiled_main}"
export FULL_MAIN_LORA="${FULL_MAIN_LORA:-$OUT/train/run/epoch-4.safetensors}"
export DIFFSYNTH_MODEL_BASE_PATH="${DIFFSYNTH_MODEL_BASE_PATH:-$DIFFSYNTH_ROOT/models}"
export DIFFSYNTH_SKIP_DOWNLOAD="${DIFFSYNTH_SKIP_DOWNLOAD:-true}"

PY_BIN_DIR="$(dirname "$PYTHON_BIN")"
export LD_LIBRARY_PATH="$PY_BIN_DIR/../lib:${LD_LIBRARY_PATH:-}"
mkdir -p "$OUT/infer" "$OUT/logs" "$OUT/eval"

"$PYTHON_BIN" scripts/qwen_arch_control/infer_qwen_arch_incontext.py \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --lora-path "$FULL_MAIN_LORA" \
  --diffsynth-root "$DIFFSYNTH_ROOT" \
  --output-dir "$OUT/infer" \
  --num-samples "${FULL_MAIN_INFER_SAMPLES:-20}" \
  --height "${FULL_MAIN_INFER_HEIGHT:-256}" \
  --width "${FULL_MAIN_INFER_WIDTH:-256}" \
  --num-inference-steps "${FULL_MAIN_INFER_STEPS:-20}" \
  --seed "${FULL_MAIN_SEED:-7721}" \
  2>&1 | tee "$OUT/logs/infer.log"
