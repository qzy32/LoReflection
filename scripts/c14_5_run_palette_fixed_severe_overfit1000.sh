#!/usr/bin/env bash
set -euo pipefail

REPO=${REPO:-/wuqingyaoa800/qiuziyan/LoReflection}
DIFFSYNTH_ROOT=${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}
PYTHON_BIN=${PYTHON_BIN:-/wuqingyaoa800/qiuziyan/envs/diffsynth-qwen/bin/python}
GPU_ID=${GPU_ID:-0}
DATASET=${REPO}/outputs/semantic_repair4_medium_dataset_v2_palette_fixed
SOURCE_BASE=${REPO}/outputs/qwen_semantic_repair4_palette_fixed_v1
OUTPUT_BASE=${REPO}/outputs/qwen_semantic_repair4_palette_fixed_overfit1000_v1
REVIEW_BASE=${REPO}/outputs/manual_review/c14_5_palette_fixed_overfit1000
REPORT_BASE=${OUTPUT_BASE}/reports
EVAL_SCRIPT=${EVAL_SCRIPT:-/tmp/loreflection_c14_4_eval/evaluate_c13_semantic_repair4_outputs.py}
RUN_LOG=${OUTPUT_BASE}/c14_5_overfit1000_daemon.log

MODEL_BASE=/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models
MODEL_ID_WITH_ORIGIN_PATHS="Qwen/Qwen-Image:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image:text_encoder/model*.safetensors,Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors,DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint:model.safetensors"
LORA_TARGET_MODULES="to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1"

mkdir -p "${OUTPUT_BASE}" "${REVIEW_BASE}" "${REPORT_BASE}"
exec > >(tee -a "${RUN_LOG}") 2>&1

gpu_snapshot() {
  nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu \
    --format=csv,noheader,nounits
}

train_action() {
  local action="$1"
  local lower
  lower=$(printf '%s' "${action}" | tr '[:upper:]' '[:lower:]')
  local source_run="${SOURCE_BASE}/${action}_20/c14_4_fixedsteps_gpu0_rank32_300steps/run"
  local resume_dir="${source_run}/resume/step-000300"
  local metadata="${DATASET}/metadata_${lower}.csv"
  local output_root="${OUTPUT_BASE}/${action}_20/c14_5_resume300_to1000_gpu${GPU_ID}_rank32"
  local run_dir="${output_root}/run"
  local log_dir="${output_root}/logs"
  local final_ckpt="${run_dir}/step-1000.safetensors"
  local eval_report="${REPORT_BASE}/${action}_step1000_eval.json"

  if [[ -f "${final_ckpt}" && -f "${eval_report}" ]]; then
    echo "$(date -Is) SKIP ${action}: step-1000 checkpoint and evaluation already exist"
    return 0
  fi

  if [[ ! -d "${resume_dir}" ]]; then
    echo "Missing resume checkpoint: ${resume_dir}" >&2
    return 2
  fi
  if [[ ! -f "${metadata}" ]]; then
    echo "Missing metadata: ${metadata}" >&2
    return 2
  fi
  mkdir -p "${run_dir}" "${log_dir}"

  echo "$(date -Is) START ${action}: exact optimizer/model resume at global step 300"
  echo "Compact schedule: repeat=36, resume epoch=14 batch=20, process remaining 700 batches, finish at global step 1000"
  cd "${DIFFSYNTH_ROOT}"
  export CUDA_VISIBLE_DEVICES="${GPU_ID}"
  export DIFFSYNTH_MODEL_BASE_PATH="${MODEL_BASE}"
  export DIFFSYNTH_SKIP_DOWNLOAD=true
  export TOKENIZERS_PARALLELISM=false

  "${PYTHON_BIN}" examples/qwen_image/model_training/train.py \
    --dataset_base_path "${DATASET}" \
    --dataset_metadata_path "${metadata}" \
    --data_file_keys "image,blockwise_controlnet_image,blockwise_controlnet_inpaint_mask" \
    --max_pixels 262144 \
    --dataset_repeat 36 \
    --per_device_batch_size 1 \
    --dataset_num_workers 0 \
    --model_id_with_origin_paths "${MODEL_ID_WITH_ORIGIN_PATHS}" \
    --learning_rate 1e-4 \
    --num_epochs 15 \
    --seed 4411 \
    --console_log_interval 1 \
    --tensorboard_log_interval 1 \
    --validation_eval_num_batches 0 \
    --validation_every_n_epochs 0 \
    --validation_every_n_steps 0 \
    --metrics_jsonl_path "${log_dir}/train_metrics.jsonl" \
    --remove_prefix_in_ckpt "pipe.dit." \
    --output_path "${run_dir}" \
    --resume_from_checkpoint "${resume_dir}" \
    --lora_base_model "dit" \
    --lora_target_modules "${LORA_TARGET_MODULES}" \
    --lora_rank 32 \
    --extra_inputs "blockwise_controlnet_image,blockwise_controlnet_inpaint_mask" \
    --use_gradient_checkpointing \
    --find_unused_parameters \
    2>&1 | tee "${log_dir}/train.log"

  local epoch_ckpt="${run_dir}/epoch-14.safetensors"
  if [[ ! -f "${epoch_ckpt}" ]]; then
    echo "Expected final LoRA missing: ${epoch_ckpt}" >&2
    return 3
  fi
  cp -f "${epoch_ckpt}" "${final_ckpt}"

  echo "$(date -Is) EVAL ${action}: all 20 training rows at step 1000"
  CUDA_VISIBLE_DEVICES="${GPU_ID}" "${PYTHON_BIN}" "${EVAL_SCRIPT}" infer-action \
    --repo "${REPO}" \
    --action "${action}" \
    --metadata "${metadata}" \
    --lora "${final_ckpt}" \
    --out-root "${REVIEW_BASE}/${action}_20" \
    --run-name "step1000_trainset_eval" \
    --max-rows 20 \
    --inference-steps 12 \
    --seed 4411 \
    > "${eval_report}"

  "${PYTHON_BIN}" - "${action}" "${output_root}" "${eval_report}" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

action, output_root, eval_report = sys.argv[1:4]
root = Path(output_root)
metrics_path = root / "logs" / "train_metrics.jsonl"
rows = []
if metrics_path.exists():
    for line in metrics_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
last = rows[-1] if rows else {}
evaluation = {}
if Path(eval_report).exists():
    raw_eval = Path(eval_report).read_text(encoding="utf-8", errors="ignore")
    try:
        evaluation = json.loads(raw_eval)
    except json.JSONDecodeError:
        evaluation = {
            "parse_status": "NON_JSON_STDOUT",
            "raw_report_path": eval_report,
            "note": "Inference completed, but stdout contains model-loading text in addition to JSON.",
        }
result = {
    "schema_version": "c14-5-severe-overfit1000-action-v1",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "action": action,
    "status": "COMPLETE",
    "resume_from_global_step": 300,
    "final_global_step": last.get("step"),
    "final_loss": last.get("loss"),
    "checkpoint": str(root / "run" / "step-1000.safetensors"),
    "evaluation": evaluation,
}
(Path(eval_report).parent / f"{action}_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
PY
  echo "$(date -Is) COMPLETE ${action}"
}

echo "$(date -Is) C14.5 severe-overfit daemon starting on physical GPU ${GPU_ID}"
gpu_snapshot
for action in REMOVE REPLACE TRANSLATE ADD; do
  train_action "${action}"
done
echo "$(date -Is) C14.5 COMPLETE: REMOVE REPLACE TRANSLATE ADD"
gpu_snapshot
