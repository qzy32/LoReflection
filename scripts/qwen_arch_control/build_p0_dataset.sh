#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

QWEN_SOURCE_MODE="${QWEN_SOURCE_MODE:-raw_3dfront}"
QWEN_3DFRONT_ROOT="${QWEN_3DFRONT_ROOT:-/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front}"
QWEN_OUTPUT_ROOT="${QWEN_OUTPUT_ROOT:-data/loreflection_qwen_arch_control_real_p0}"

python -m loreflection.qwen_arch_control.build_qwen_arch_control_dataset \
  --source-mode "$QWEN_SOURCE_MODE" \
  --data-root "$QWEN_3DFRONT_ROOT" \
  --output-root "$QWEN_OUTPUT_ROOT" \
  --num-samples "${P0_NUM_SAMPLES:-60}" \
  --image-size "${P0_IMAGE_SIZE:-256}" \
  --seed "${P0_SEED:-4411}"

python tools/validate_arch_incontext_training_metadata.py \
  "$QWEN_OUTPUT_ROOT/metadata.csv" \
  --dataset-base "$QWEN_OUTPUT_ROOT" \
  --output "$QWEN_OUTPUT_ROOT/audits/metadata_validator_report.json"

python -m loreflection.qwen_arch_control.audit_palette_exact "$QWEN_OUTPUT_ROOT"
python -m loreflection.qwen_arch_control.audit_prompt_no_coordinate_leakage "$QWEN_OUTPUT_ROOT"
python -m loreflection.qwen_arch_control.audit_qwen_arch_control_dataset "$QWEN_OUTPUT_ROOT"
python -m loreflection.qwen_arch_control.preview_qwen_arch_dataset "$QWEN_OUTPUT_ROOT"
