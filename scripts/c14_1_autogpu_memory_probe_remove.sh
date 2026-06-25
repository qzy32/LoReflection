#!/usr/bin/env bash
set -euo pipefail

# Server-side one-row memory probe for C14.1 REMOVE.
# Requires CUDA_VISIBLE_DEVICES to be set by the caller.

if [[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  echo "CUDA_VISIBLE_DEVICES must be set before running this probe." >&2
  exit 2
fi

DIFFSYNTH_ROOT="${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}"
PYTHON_BIN="${PYTHON_BIN:-/wuqingyaoa800/qiuziyan/envs/diffsynth-qwen/bin/python}"
DATASET_BASE="/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v1"
MODEL_BASE="/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models"
OUTPUT_ROOT="/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/REMOVE_20/autogpu_memory_probe"
PROBE_METADATA="${DATASET_BASE}/metadata_remove_probe_1row.csv"
MODEL_ID_WITH_ORIGIN_PATHS="Qwen/Qwen-Image:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image:text_encoder/model*.safetensors,Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors,DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint:model.safetensors"
LORA_TARGET_MODULES="to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1"

mkdir -p "${OUTPUT_ROOT}/logs"
if [[ ! -f "${PROBE_METADATA}" ]]; then
  head -n 2 "${DATASET_BASE}/metadata_remove.csv" > "${PROBE_METADATA}"
fi

cd "${DIFFSYNTH_ROOT}"
export DIFFSYNTH_MODEL_BASE_PATH="${MODEL_BASE}"
export DIFFSYNTH_SKIP_DOWNLOAD=true
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

"${PYTHON_BIN}" examples/qwen_image/model_training/train.py \
  --dataset_base_path "${DATASET_BASE}" \
  --dataset_metadata_path "${PROBE_METADATA}" \
  --data_file_keys "image,blockwise_controlnet_image,blockwise_controlnet_inpaint_mask" \
  --max_pixels 262144 \
  --dataset_repeat 1 \
  --per_device_batch_size 1 \
  --dataset_num_workers 0 \
  --model_id_with_origin_paths "${MODEL_ID_WITH_ORIGIN_PATHS}" \
  --learning_rate 1e-4 \
  --num_epochs 1 \
  --save_steps 999 \
  --seed 4411 \
  --console_log_interval 1 \
  --tensorboard_log_interval 999 \
  --validation_eval_num_batches 0 \
  --validation_every_n_epochs 0 \
  --validation_every_n_steps 0 \
  --metrics_jsonl_path "${OUTPUT_ROOT}/logs/train_metrics.jsonl" \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path "${OUTPUT_ROOT}/run" \
  --lora_base_model "dit" \
  --lora_target_modules "${LORA_TARGET_MODULES}" \
  --lora_rank 32 \
  --extra_inputs "blockwise_controlnet_image,blockwise_controlnet_inpaint_mask" \
  --use_gradient_checkpointing \
  --find_unused_parameters \
  2>&1 | tee "${OUTPUT_ROOT}/logs/train.log"
