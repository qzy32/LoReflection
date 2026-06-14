#!/usr/bin/env bash
# Server-only template for DiffSynth-Studio Qwen-Image Blockwise ControlNet Inpaint LoRA.
# Do not run locally. Fill all /server/path placeholders on the training server.

set -euo pipefail

DIFFSYNTH_DIR="/server/path/to/DiffSynth-Studio"
DATA_DIR="/server/path/to/data/loreflection_diffsynth_inpaint"
MODEL_PATH="/server/path/to/Qwen-Image"
OUTPUT_DIR="/server/path/to/outputs/loreflection_qwen_image_inpaint_lora"

cd "${DIFFSYNTH_DIR}"

python examples/qwen_image/train_qwen_image_blockwise_controlnet_inpaint.py \
  --model_path "${MODEL_PATH}" \
  --dataset_base_path "${DATA_DIR}" \
  --metadata_file "${DATA_DIR}/metadata.csv" \
  --output_path "${OUTPUT_DIR}" \
  --train_lora true

