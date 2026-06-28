#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
DATASET_BASE="${P0_DATASET_BASE:-$ROOT/data/loreflection_qwen_arch_control_real_p0}"
METADATA="$DATASET_BASE/metadata.csv"
OUT="${P0_SANITY_OUTPUT_ROOT:-$ROOT/outputs/qwen_arch_incontext_p0_sanity}"
mkdir -p "$OUT/preflight" "$OUT/subsets" "$OUT/train_tiny" "$OUT/train_p0_50" "$OUT/logs" "$OUT/eval" "$OUT/infer" "$OUT/quantized"

FIELD_LOG="$ROOT/reports/p0_sanity/FIELD_ADJUSTMENT_LOG.md"
mkdir -p "$(dirname "$FIELD_LOG")"
cat > "$FIELD_LOG" <<'EOF'
# P0 Sanity Field Adjustment Log

- Core metadata semantics preserved: image=target_full_semantic, prompt=compiled_text_prompt, context_image=architecture_condition_image.
- Training uses `--data_file_keys "image,context_image"` and `--extra_inputs "context_image"`.
- max_pixels is set to 65536 because P0-real images are 256x256.
- dataset_num_workers is set to 0 for a conservative server sanity run.
- per_device_batch_size is not passed because the current DiffSynth train.py does not expose that argument; it uses the DiffSynth training default.
- model loading uses DiffSynth model_id_with_origin_paths with DIFFSYNTH_MODEL_BASE_PATH and DIFFSYNTH_SKIP_DOWNLOAD=true so local Qwen/Qwen-Image files are used without network access.
- LD_LIBRARY_PATH is prefixed with the selected conda environment lib directory so DiffSynth-Studio uses the matching libstdc++/PIL runtime.
- This run uses the Qwen Architecture In-Context metadata contract.
EOF

find_diffsynth() {
  if [ -n "${DIFFSYNTH_ROOT:-}" ] && [ -f "$DIFFSYNTH_ROOT/examples/qwen_image/model_training/train.py" ]; then
    echo "$DIFFSYNTH_ROOT"; return 0
  fi
  for d in \
    /wuqingyaoa800/qiuziyan/DiffSynth-Studio \
    /wuqingyaoa800/qiuziyan/LoReflection/DiffSynth-Studio \
    /wuqingyaoa800/qiuziyan/LoReflection_arch_p0/DiffSynth-Studio; do
    if [ -f "$d/examples/qwen_image/model_training/train.py" ]; then
      echo "$d"; return 0
    fi
  done
  return 1
}

if [ -z "${PYTHON_BIN:-}" ]; then
  for py in \
    /home/chengjiajia/anaconda3/envs/DiffSynth-Studio/bin/python \
    /home/chengjiajia/anaconda3/envs/qwen-image/bin/python \
    /opt/conda/bin/python; do
    if [ -x "$py" ]; then
      PYTHON_BIN="$py"
      break
    fi
  done
fi
PYTHON_BIN="${PYTHON_BIN:-$(command -v python || true)}"
PY_BIN_DIR="$(dirname "$PYTHON_BIN")"
export PATH="$PY_BIN_DIR:$PATH"
export LD_LIBRARY_PATH="$PY_BIN_DIR/../lib:${LD_LIBRARY_PATH:-}"
ACCELERATE_BIN="${ACCELERATE_BIN:-$PY_BIN_DIR/accelerate}"
if [ ! -x "$ACCELERATE_BIN" ]; then
  ACCELERATE_BIN="$(command -v accelerate || true)"
fi
if [ -z "${CUDA_VISIBLE_DEVICES:-}" ] && command -v nvidia-smi >/dev/null 2>&1; then
  CUDA_VISIBLE_DEVICES="$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | awk -F, '{gsub(/ /,"",$1); gsub(/ /,"",$2); print $2" "$1}' | sort -nr | head -1 | awk '{print $2}')"
  export CUDA_VISIBLE_DEVICES
fi
DIFFSYNTH_ROOT="$(find_diffsynth || true)"
TRAIN_PY="$DIFFSYNTH_ROOT/examples/qwen_image/model_training/train.py"
UNION_LORA_REL="models/DiffSynth-Studio/Qwen-Image-In-Context-Control-Union/model.safetensors"
UNION_LORA="$DIFFSYNTH_ROOT/$UNION_LORA_REL"
if [ ! -f "$UNION_LORA" ] && [ -n "${DIFFSYNTH_MODEL_BASE_PATH:-}" ]; then
  UNION_LORA="$DIFFSYNTH_MODEL_BASE_PATH/DiffSynth-Studio/Qwen-Image-In-Context-Control-Union/model.safetensors"
fi
export DIFFSYNTH_MODEL_BASE_PATH="${DIFFSYNTH_MODEL_BASE_PATH:-$DIFFSYNTH_ROOT/models}"
export DIFFSYNTH_SKIP_DOWNLOAD="${DIFFSYNTH_SKIP_DOWNLOAD:-true}"

{
  echo "repo_root=$ROOT"
  echo "dataset_base=$DATASET_BASE"
  echo "metadata=$METADATA"
  echo "diffsynth_root=$DIFFSYNTH_ROOT"
  echo "python_bin=$PYTHON_BIN"
  echo "accelerate_bin=$ACCELERATE_BIN"
  echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-}"
  echo "train_py=$TRAIN_PY"
  echo "union_lora=$UNION_LORA"
  echo "nvidia_smi=$(command -v nvidia-smi || true)"
  command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi --query-gpu=index,name,memory.free,memory.used,utilization.gpu --format=csv,noheader || true
  "$PYTHON_BIN" - <<'PY'
import json, shutil, subprocess, sys, os
print("python_version=" + sys.version.replace("\n", " "))
print("accelerate=" + os.environ.get("ACCELERATE_BIN", shutil.which("accelerate") or ""))
PY
  grep -q "extra_inputs" "$TRAIN_PY" && echo "train_py_supports_extra_inputs=true" || echo "train_py_supports_extra_inputs=false"
  grep -q "context_image" "$DIFFSYNTH_ROOT/diffsynth/core/data/unified_dataset.py" && echo "unified_dataset_mentions_context_image=true" || echo "unified_dataset_mentions_context_image=false"
} > "$OUT/logs/preflight.log" 2>&1 || true

"$PYTHON_BIN" - <<PY
import json, os, shutil
from pathlib import Path
report = {
  "diffsynth_root": "$DIFFSYNTH_ROOT",
  "train_py_exists": Path("$TRAIN_PY").exists(),
  "python_bin": "$PYTHON_BIN",
  "accelerate_bin": "$ACCELERATE_BIN",
  "accelerate_available": Path("$ACCELERATE_BIN").exists(),
  "cuda_visible_devices": "${CUDA_VISIBLE_DEVICES:-}",
  "gpu_visible": shutil.which("nvidia-smi") is not None,
  "union_lora": "$UNION_LORA",
  "union_lora_exists": Path("$UNION_LORA").exists(),
  "train_py_supports_extra_inputs": "extra_inputs" in Path("$TRAIN_PY").read_text(errors="ignore") if Path("$TRAIN_PY").exists() else False,
  "supports_context_image_extra_input": "context_image" in (Path("$DIFFSYNTH_ROOT") / "diffsynth/core/data/unified_dataset.py").read_text(errors="ignore") if Path("$DIFFSYNTH_ROOT", "diffsynth/core/data/unified_dataset.py").exists() else False,
  "metadata": "$METADATA",
}
report["status"] = "pass" if all([report["train_py_exists"], report["accelerate_available"], report["union_lora_exists"], report["train_py_supports_extra_inputs"]]) else "fail"
Path("$OUT/preflight/preflight_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["status"] == "pass" else 1)
PY

"$PYTHON_BIN" "$ROOT/scripts/qwen_arch_control/make_p0_sanity_subsets.py" \
  --metadata "$METADATA" \
  --dataset-base "$DATASET_BASE" \
  --output-dir "$OUT/subsets" \
  --tiny-count 8 | tee "$OUT/logs/make_subsets.log"

cd "$DIFFSYNTH_ROOT"

COMMON_ARGS=(
  examples/qwen_image/model_training/train.py
  --dataset_base_path "$DATASET_BASE"
  --data_file_keys "image,context_image"
  --max_pixels 65536
  --dataset_num_workers 0
  --model_id_with_origin_paths "Qwen/Qwen-Image:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image:text_encoder/model*.safetensors,Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors"
  --tokenizer_path "$DIFFSYNTH_ROOT/models/Qwen/Qwen-Image/tokenizer"
  --processor_path "$DIFFSYNTH_ROOT/models/Qwen/Qwen-Image-Edit/processor"
  --learning_rate 1e-4
  --remove_prefix_in_ckpt "pipe.dit."
  --lora_base_model "dit"
  --lora_target_modules "to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1"
  --lora_rank 64
  --lora_checkpoint "$UNION_LORA"
  --extra_inputs "context_image"
  --use_gradient_checkpointing
  --find_unused_parameters
)

echo "$ACCELERATE_BIN launch ${COMMON_ARGS[*]} --dataset_metadata_path $OUT/subsets/p0_tiny_8.csv --dataset_repeat 5 --num_epochs 1 --output_path $OUT/train_tiny/run" > "$OUT/logs/train_tiny_command.txt"
"$ACCELERATE_BIN" launch "${COMMON_ARGS[@]}" \
  --dataset_metadata_path "$OUT/subsets/p0_tiny_8.csv" \
  --dataset_repeat 5 \
  --num_epochs 1 \
  --output_path "$OUT/train_tiny/run" \
  2>&1 | tee "$OUT/logs/train_tiny.log"

echo "$ACCELERATE_BIN launch ${COMMON_ARGS[*]} --dataset_metadata_path $OUT/subsets/p0_50.csv --dataset_repeat ${P0_DATASET_REPEAT:-20} --num_epochs ${P0_NUM_EPOCHS:-3} --output_path $OUT/train_p0_50/run" > "$OUT/logs/train_p0_50_command.txt"
"$ACCELERATE_BIN" launch "${COMMON_ARGS[@]}" \
  --dataset_metadata_path "$OUT/subsets/p0_50.csv" \
  --dataset_repeat "${P0_DATASET_REPEAT:-20}" \
  --num_epochs "${P0_NUM_EPOCHS:-3}" \
  --output_path "$OUT/train_p0_50/run" \
  2>&1 | tee "$OUT/logs/train_p0_50.log"

cd "$ROOT"
bash scripts/qwen_arch_control/run_p0_sanity_infer.sh
"$PYTHON_BIN" scripts/qwen_arch_control/quantize_qwen_output_palette.py \
  --input-dir "$OUT/infer" \
  --output-dir "$OUT/quantized" \
  --report "$OUT/eval/palette_quantization_report.json"
"$PYTHON_BIN" scripts/qwen_arch_control/evaluate_p0_sanity_outputs.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_BASE" \
  --metadata "$OUT/subsets/p0_50.csv" \
  --train-log "$OUT/logs/train_tiny_command.txt" \
  --train-log "$OUT/logs/train_p0_50_command.txt" \
  --train-log "$OUT/logs/train_tiny.log" \
  --train-log "$OUT/logs/train_p0_50.log" \
  --script "$ROOT/scripts/qwen_arch_control/run_p0_sanity_train.sh"

cat > "$OUT/P0_SANITY_TRAINING_SUMMARY.md" <<EOF
# P0 Sanity Training Summary

- Dataset package: \`$DATASET_BASE\`
- Metadata: \`$METADATA\`
- Tiny training: completed if \`logs/train_tiny.log\` ends without error
- P0_50 training: completed if \`logs/train_p0_50.log\` ends without error
- DiffSynth root: \`$DIFFSYNTH_ROOT\`
- Python: \`$PYTHON_BIN\`
- GPU: see \`logs/preflight.log\`
- Train commands: \`logs/train_tiny_command.txt\`, \`logs/train_p0_50_command.txt\`
- Checkpoint path: \`train_p0_50/run\`
- Train logs: \`logs/train_tiny.log\`, \`logs/train_p0_50.log\`
- Uses context_image: yes
- Training command contract: see \`eval/training_command_contract_check.json\`
- Inference samples: \`infer/\`
- Quantized outputs: \`quantized/\`
- Eval report: \`eval/p0_sanity_eval_report.json\`
- overfit_success: see eval report
- Next step: if train passes but inference remains TODO, implement verified DiffSynth Architecture In-Context inference wrapper before P1.
EOF
