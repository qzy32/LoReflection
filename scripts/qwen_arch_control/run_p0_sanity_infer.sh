#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export DIFFSYNTH_ROOT="${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}"
export PYTHON_BIN="${PYTHON_BIN:-/home/chengjiajia/anaconda3/envs/DiffSynth-Studio/bin/python}"
export DATASET_ROOT="${DATASET_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_real_p0}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata.csv}"
export P0_LORA="${P0_LORA:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/train_p0_50/run/epoch-2.safetensors}"
export OUT="${OUT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity}"
export DIFFSYNTH_MODEL_BASE_PATH="${DIFFSYNTH_MODEL_BASE_PATH:-$DIFFSYNTH_ROOT/models}"
export DIFFSYNTH_SKIP_DOWNLOAD="${DIFFSYNTH_SKIP_DOWNLOAD:-true}"
PY_BIN_DIR="$(dirname "$PYTHON_BIN")"
export LD_LIBRARY_PATH="$PY_BIN_DIR/../lib:${LD_LIBRARY_PATH:-}"

mkdir -p "$OUT/infer" "$OUT/logs" reports/p0_sanity

"$PYTHON_BIN" scripts/qwen_arch_control/infer_qwen_arch_incontext.py \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --lora-path "$P0_LORA" \
  --diffsynth-root "$DIFFSYNTH_ROOT" \
  --output-dir "$OUT/infer" \
  --num-samples "${P0_INFER_SAMPLES:-10}" \
  --height "${P0_INFER_HEIGHT:-256}" \
  --width "${P0_INFER_WIDTH:-256}" \
  --num-inference-steps "${P0_INFER_STEPS:-20}" \
  --seed "${P0_SEED:-4411}" \
  2>&1 | tee "$OUT/logs/infer.log"
