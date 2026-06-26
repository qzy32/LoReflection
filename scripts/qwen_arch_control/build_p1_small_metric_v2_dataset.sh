#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export QWEN_SOURCE_MODE="${QWEN_SOURCE_MODE:-raw_3dfront}"
export QWEN_3DFRONT_ROOT="${QWEN_3DFRONT_ROOT:-/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front}"
export QWEN_OUTPUT_ROOT="${QWEN_OUTPUT_ROOT:-data/loreflection_qwen_arch_control_p1_small_metric_v2}"
export P1_NUM_SAMPLES="${P1_NUM_SAMPLES:-200}"
export P1_IMAGE_SIZE="${P1_IMAGE_SIZE:-256}"
export P1_SEED="${P1_SEED:-5521}"
export QWEN_RENDERER_VERSION="${QWEN_RENDERER_VERSION:-metric_v2}"
export QWEN_CANVAS_EXTENT_M="${QWEN_CANVAS_EXTENT_M:-8.0}"
/home/chengjiajia/anaconda3/bin/python -m loreflection.qwen_arch_control.build_qwen_arch_control_dataset \
  --source-mode "$QWEN_SOURCE_MODE" \
  --data-root "$QWEN_3DFRONT_ROOT" \
  --output-root "$QWEN_OUTPUT_ROOT" \
  --num-samples "$P1_NUM_SAMPLES" \
  --image-size "$P1_IMAGE_SIZE" \
  --seed "$P1_SEED" \
  --renderer-version "$QWEN_RENDERER_VERSION" \
  --canvas-extent-m "$QWEN_CANVAS_EXTENT_M"
/home/chengjiajia/anaconda3/bin/python -m loreflection.qwen_arch_control.audit_architecture_condition_scale "$QWEN_OUTPUT_ROOT"
