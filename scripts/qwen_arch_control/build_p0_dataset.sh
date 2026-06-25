#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python -m loreflection.qwen_arch_control.build_qwen_arch_control_dataset \
  --output-root data/loreflection_qwen_arch_control \
  --num-samples "${P0_NUM_SAMPLES:-60}" \
  --image-size "${P0_IMAGE_SIZE:-256}" \
  --seed "${P0_SEED:-4411}"

python tools/validate_arch_incontext_training_metadata.py \
  data/loreflection_qwen_arch_control/metadata.csv \
  --dataset-base data/loreflection_qwen_arch_control \
  --output data/loreflection_qwen_arch_control/audits/metadata_validator_report.json

python -m loreflection.qwen_arch_control.audit_palette_exact data/loreflection_qwen_arch_control
python -m loreflection.qwen_arch_control.audit_prompt_no_coordinate_leakage data/loreflection_qwen_arch_control
python -m loreflection.qwen_arch_control.audit_qwen_arch_control_dataset data/loreflection_qwen_arch_control
python -m loreflection.qwen_arch_control.preview_qwen_arch_dataset data/loreflection_qwen_arch_control
