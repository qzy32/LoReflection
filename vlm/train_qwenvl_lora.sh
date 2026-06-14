#!/usr/bin/env bash
# Server-only template for Qwen-VL LoRA SFT.
# Do not run locally. Fill paths on the training server.

set -euo pipefail

QWEN_VL_FINETUNE_DIR="/server/path/to/qwen-vl-finetune"
MODEL_PATH="/server/path/to/Qwen2.5-VL"
DATA_JSON="/server/path/to/loreflection/qwenvl_sft.json"
OUTPUT_DIR="/server/path/to/outputs/loreflection_qwenvl_lora"

cd "${QWEN_VL_FINETUNE_DIR}"

python train.py \
  --model_name_or_path "${MODEL_PATH}" \
  --data_path "${DATA_JSON}" \
  --output_dir "${OUTPUT_DIR}" \
  --use_lora true

