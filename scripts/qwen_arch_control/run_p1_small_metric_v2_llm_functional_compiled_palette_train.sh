#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=${REPO_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0}
DIFFSYNTH_ROOT=${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}
DATASET_ROOT=${DATASET_ROOT:-$REPO_ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm}
METADATA=${METADATA:-$DATASET_ROOT/metadata_llm_functional_compiled_palette.csv}
OUT=${OUT:-$REPO_ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional_compiled_palette}
INIT_LORA=${INIT_LORA:-$REPO_ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2/train/run/epoch-2.safetensors}
PYTHON_BIN=${PYTHON_BIN:-python}

mkdir -p "$OUT/logs" "$OUT/train"
cd "$DIFFSYNTH_ROOT"

accelerate launch examples/qwen_image/model_training/train.py \
  --dataset_base_path "$DATASET_ROOT" \
  --dataset_metadata_path "$METADATA" \
  --data_file_keys "image,context_image" \
  --max_pixels 65536 \
  --dataset_repeat 10 \
  --per_device_batch_size 1 \
  --dataset_num_workers 0 \
  --model_id_with_origin_paths "Qwen/Qwen-Image:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image:text_encoder/model*.safetensors,Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors" \
  --learning_rate 1e-4 \
  --num_epochs 3 \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path "$OUT/train/run" \
  --lora_base_model "dit" \
  --lora_target_modules "to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1" \
  --lora_rank 64 \
  --lora_checkpoint "$INIT_LORA" \
  --extra_inputs "context_image" \
  --use_gradient_checkpointing \
  --find_unused_parameters \
  2>&1 | tee "$OUT/logs/train.log"
