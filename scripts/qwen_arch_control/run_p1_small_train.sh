#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export DIFFSYNTH_ROOT="${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}"
export PYTHON_BIN="${PYTHON_BIN:-/home/chengjiajia/anaconda3/envs/DiffSynth-Studio/bin/python}"
export ACCELERATE_BIN="${ACCELERATE_BIN:-/home/chengjiajia/anaconda3/envs/DiffSynth-Studio/bin/accelerate}"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_p1_small}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_p1_small}"
export INIT_LORA="${INIT_LORA:-$ROOT/outputs/qwen_arch_incontext_p0_sanity/train_p0_50/run/epoch-2.safetensors}"
export EXPECTED_LORA_FAMILY="Qwen-Image-In-Context-Control-Union"
export DIFFSYNTH_MODEL_BASE_PATH="${DIFFSYNTH_MODEL_BASE_PATH:-$DIFFSYNTH_ROOT/models}"
export DIFFSYNTH_SKIP_DOWNLOAD="${DIFFSYNTH_SKIP_DOWNLOAD:-true}"
export P1_DATASET_REPEAT="${P1_DATASET_REPEAT:-10}"
export P1_NUM_EPOCHS="${P1_NUM_EPOCHS:-3}"
export P1_MAX_PIXELS="${P1_MAX_PIXELS:-65536}"
export P1_LR="${P1_LR:-1e-4}"
export P1_LORA_RANK="${P1_LORA_RANK:-64}"
PY_BIN_DIR="$(dirname "$PYTHON_BIN")"
export LD_LIBRARY_PATH="$PY_BIN_DIR/../lib:${LD_LIBRARY_PATH:-}"
mkdir -p "$OUT/logs" "$OUT/train/run" "$OUT/eval" reports/p1_small
TRAIN_PY="$DIFFSYNTH_ROOT/examples/qwen_image/model_training/train.py"
if [ ! -f "$TRAIN_PY" ]; then echo "missing train.py: $TRAIN_PY" >&2; exit 2; fi
if [ ! -f "$INIT_LORA" ]; then echo "missing init lora: $INIT_LORA" >&2; exit 3; fi
if [ ! -f "$METADATA" ]; then echo "missing metadata: $METADATA" >&2; exit 4; fi
cat > "$OUT/logs/train_command.txt" <<EOF
cd "$DIFFSYNTH_ROOT"
DIFFSYNTH_MODEL_BASE_PATH="$DIFFSYNTH_MODEL_BASE_PATH"
DIFFSYNTH_SKIP_DOWNLOAD="$DIFFSYNTH_SKIP_DOWNLOAD"
$ACCELERATE_BIN launch examples/qwen_image/model_training/train.py \\
  --dataset_base_path "$DATASET_ROOT" \\
  --dataset_metadata_path "$METADATA" \\
  --data_file_keys "image,context_image" \\
  --max_pixels "$P1_MAX_PIXELS" \\
  --dataset_repeat "$P1_DATASET_REPEAT" \\
  --dataset_num_workers 0 \\
  --model_id_with_origin_paths "Qwen/Qwen-Image:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image:text_encoder/model*.safetensors,Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors" \\
  --tokenizer_path "models/Qwen/Qwen-Image/tokenizer" \\
  --processor_path "models/Qwen/Qwen-Image-Edit/processor" \\
  --learning_rate "$P1_LR" \\
  --num_epochs "$P1_NUM_EPOCHS" \\
  --remove_prefix_in_ckpt "pipe.dit." \\
  --output_path "$OUT/train/run" \\
  --lora_base_model "dit" \\
  --lora_target_modules "to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1" \\
  --lora_rank "$P1_LORA_RANK" \\
  --lora_checkpoint "$INIT_LORA" \\
  --extra_inputs "context_image" \\
  --use_gradient_checkpointing \\
  --find_unused_parameters
EOF
cd "$DIFFSYNTH_ROOT"
"$ACCELERATE_BIN" launch examples/qwen_image/model_training/train.py \
  --dataset_base_path "$DATASET_ROOT" \
  --dataset_metadata_path "$METADATA" \
  --data_file_keys "image,context_image" \
  --max_pixels "$P1_MAX_PIXELS" \
  --dataset_repeat "$P1_DATASET_REPEAT" \
  --dataset_num_workers 0 \
  --model_id_with_origin_paths "Qwen/Qwen-Image:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image:text_encoder/model*.safetensors,Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors" \
  --tokenizer_path "models/Qwen/Qwen-Image/tokenizer" \
  --processor_path "models/Qwen/Qwen-Image-Edit/processor" \
  --learning_rate "$P1_LR" \
  --num_epochs "$P1_NUM_EPOCHS" \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path "$OUT/train/run" \
  --lora_base_model "dit" \
  --lora_target_modules "to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1" \
  --lora_rank "$P1_LORA_RANK" \
  --lora_checkpoint "$INIT_LORA" \
  --extra_inputs "context_image" \
  --use_gradient_checkpointing \
  --find_unused_parameters \
  2>&1 | tee "$OUT/logs/train.log"
