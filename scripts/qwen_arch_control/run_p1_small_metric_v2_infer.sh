#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export DIFFSYNTH_ROOT="${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}"
export PYTHON_BIN="${PYTHON_BIN:-/home/chengjiajia/anaconda3/envs/DiffSynth-Studio/bin/python}"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2}"
export P1_METRIC_V2_LORA="${P1_METRIC_V2_LORA:-$OUT/train/run/epoch-2.safetensors}"
export DIFFSYNTH_MODEL_BASE_PATH="${DIFFSYNTH_MODEL_BASE_PATH:-$DIFFSYNTH_ROOT/models}"
export DIFFSYNTH_SKIP_DOWNLOAD="${DIFFSYNTH_SKIP_DOWNLOAD:-true}"
PY_BIN_DIR="$(dirname "$PYTHON_BIN")"
export LD_LIBRARY_PATH="$PY_BIN_DIR/../lib:${LD_LIBRARY_PATH:-}"
mkdir -p "$OUT/infer" "$OUT/logs" "$OUT/eval"
"$PYTHON_BIN" scripts/qwen_arch_control/infer_qwen_arch_incontext.py \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --lora-path "$P1_METRIC_V2_LORA" \
  --diffsynth-root "$DIFFSYNTH_ROOT" \
  --output-dir "$OUT/infer" \
  --num-samples "${P1_METRIC_V2_INFER_SAMPLES:-20}" \
  --height "${P1_METRIC_V2_INFER_HEIGHT:-256}" \
  --width "${P1_METRIC_V2_INFER_WIDTH:-256}" \
  --num-inference-steps "${P1_METRIC_V2_INFER_STEPS:-20}" \
  --seed "${P1_METRIC_V2_SEED:-6611}" \
  2>&1 | tee "$OUT/logs/infer.log"
