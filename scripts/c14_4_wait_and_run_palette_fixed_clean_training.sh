#!/usr/bin/env bash
set -euo pipefail

REPO=${REPO:-/wuqingyaoa800/qiuziyan/LoReflection}
DIFFSYNTH_ROOT=${DIFFSYNTH_ROOT:-/wuqingyaoa800/qiuziyan/DiffSynth-Studio}
PYTHON_BIN=${PYTHON_BIN:-/wuqingyaoa800/qiuziyan/envs/diffsynth-qwen/bin/python}
DATASET=${REPO}/outputs/semantic_repair4_medium_dataset_v2_palette_fixed
OUTPUT_BASE=${REPO}/outputs/qwen_semantic_repair4_palette_fixed_v1
REVIEW_BASE=${REPO}/outputs/manual_review
REPORT_DIR=${REPORT_DIR:-/tmp/loreflection_c14_4_reports}
EVAL_SCRIPT=${EVAL_SCRIPT:-/tmp/loreflection_c14_4_eval/evaluate_c13_semantic_repair4_outputs.py}
WAIT_LOG=${OUTPUT_BASE}/c14_4_wait.log
STATUS_JSON=${REPORT_DIR}/c14_4_gpu_wait_and_selection.json
PREFER_FREE_MB=${PREFER_FREE_MB:-60000}
MIN_TRY_FREE_MB=${MIN_TRY_FREE_MB:-35000}
CHECK_INTERVAL_SECONDS=${CHECK_INTERVAL_SECONDS:-300}
MAX_WAIT_CYCLES=${MAX_WAIT_CYCLES:-288}
RUN_TAG=${RUN_TAG:-c14_4_fixedsteps}

mkdir -p "${OUTPUT_BASE}" "${REPORT_DIR}" "$(dirname "${STATUS_JSON}")"
export WAIT_LOG PREFER_FREE_MB MIN_TRY_FREE_MB

write_status() {
  local status="$1"
  local detail="$2"
  "${PYTHON_BIN}" - "$STATUS_JSON" "$status" "$detail" <<'PY'
import json
import sys
from datetime import datetime, timezone
path, status, detail = sys.argv[1:4]
data = {
    "schema_version": "c14-4-gpu-wait-and-selection-v1",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "detail": detail,
    "prefer_free_memory_mb": int(__import__("os").environ.get("PREFER_FREE_MB", "60000")),
    "min_try_free_memory_mb": int(__import__("os").environ.get("MIN_TRY_FREE_MB", "35000")),
    "wait_log": __import__("os").environ.get("WAIT_LOG", ""),
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
PY
}

choose_gpu() {
  nvidia-smi --query-gpu=index,memory.free,utilization.gpu --format=csv,noheader,nounits | awk -F, -v prefer="${PREFER_FREE_MB}" -v min="${MIN_TRY_FREE_MB}" '
    {
      gsub(/ /,"",$1); gsub(/ /,"",$2); gsub(/ /,"",$3);
      idx=$1; free=$2+0; util=$3+0;
      if (free >= prefer && free > prefer_free) {prefer_idx=idx; prefer_free=free; prefer_util=util}
      if (free >= min) {
        score = free - util * 50;
        if (score > best_score) {best_idx=idx; best_free=free; best_util=util; best_score=score}
      }
    }
    END {
      if (prefer_free > 0) print prefer_idx ":" prefer_free ":" prefer_util ":prefer";
      else if (best_free > 0) print best_idx ":" best_free ":" best_util ":try";
    }'
}

train_action() {
  local action_upper="$1"
  local action_lower="$2"
  local gpu_id="$3"
  local action_dir="${action_upper}_20"
  if [[ "${action_upper}" == "MIXED" ]]; then
    action_dir="MIXED_80"
  fi
  local metadata="${DATASET}/metadata_${action_lower}.csv"
  local smoke_root="${OUTPUT_BASE}/${action_dir}/${RUN_TAG}_gpu${gpu_id}_rank32_smoke20"
  local run_root="${OUTPUT_BASE}/${action_dir}/${RUN_TAG}_gpu${gpu_id}_rank32_300steps"
  local main_epochs=15
  if [[ "${action_upper}" == "MIXED" ]]; then
    # The DiffSynth runner is epoch based. MIXED_80 reaches step-300 during
    # epoch 4 and may finish at step-320; the step-300 checkpoint is the
    # C14.4 evaluation target.
    main_epochs=4
  fi

  echo "$(date -Is) smoke ${action_upper} on GPU ${gpu_id}" | tee -a "${WAIT_LOG}"
  GPU_ID="${gpu_id}" METADATA="${metadata}" OUTPUT_ROOT="${smoke_root}" DATASET_REPEAT=1 NUM_EPOCHS=1 SAVE_STEPS=20 SEED=4411 \
    bash "${DATASET}/_scripts/c14_3_train_common.sh"

  echo "$(date -Is) 300-step ${action_upper} on GPU ${gpu_id}" | tee -a "${WAIT_LOG}"
  GPU_ID="${gpu_id}" METADATA="${metadata}" OUTPUT_ROOT="${run_root}" DATASET_REPEAT=1 NUM_EPOCHS="${main_epochs}" SAVE_STEPS=300 SEED=4411 \
    bash "${DATASET}/_scripts/c14_3_train_common.sh"

  for step in 100 300; do
    local ckpt="${run_root}/run/step-${step}.safetensors"
    if [[ -f "${ckpt}" ]]; then
      echo "$(date -Is) eval ${action_upper} step-${step}" | tee -a "${WAIT_LOG}"
      CUDA_VISIBLE_DEVICES="${gpu_id}" "${PYTHON_BIN}" "${EVAL_SCRIPT}" infer-action \
        --repo "${REPO}" \
        --action "${action_upper}" \
        --metadata "${metadata}" \
        --lora "${ckpt}" \
        --out-root "${REVIEW_BASE}/c14_4_palette_fixed_${action_dir}" \
        --run-name "step${step}_eval" \
        --max-rows 5 \
        --inference-steps 12 \
        --seed 4411 \
        > "${REPORT_DIR}/c14_4_palette_fixed_${action_upper}_20_step${step}_eval.json"
    fi
  done

  "${PYTHON_BIN}" "${EVAL_SCRIPT}" summarize-train \
    --train-root "${run_root}/.." \
    --run-name "$(basename "${run_root}")" \
    --reports "${REPORT_DIR}" \
    || true

  "${PYTHON_BIN}" - "${action_upper}" "${action_dir}" "${run_root}" "${REPORT_DIR}" "${REVIEW_BASE}/c14_4_palette_fixed_${action_dir}/c13_overfit_${action_upper}/step300_eval/metrics_by_checkpoint.json" <<'PY'
import json
import sys
from pathlib import Path
action, action_dir, run_root, report_dir, eval_json = sys.argv[1:6]
run = Path(run_root)
metrics_path = run / "logs" / "train_metrics.jsonl"
last_loss = None
if metrics_path.exists():
    for line in metrics_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        for key in ("loss", "train_loss"):
            if isinstance(obj.get(key), (int, float)):
                last_loss = obj[key]
eval_summary = {}
if Path(eval_json).exists():
    eval_summary = json.loads(Path(eval_json).read_text(encoding="utf-8"))
data = {
    "schema_version": "c14-4-palette-fixed-action-result-v1",
    "action": action,
    "status": "RUN_COMPLETE",
    "steps": 300,
    "checkpoint": str(run / "run" / "step-300.safetensors"),
    "loss": last_loss,
    "eval_summary": eval_summary,
    "gate": "CLEAN_ACTION_PARTIAL" if eval_summary else "EVAL_PENDING",
}
out = Path(report_dir) / f"c14_4_palette_fixed_{action_dir}.json"
out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
csv = Path(report_dir) / f"c14_4_palette_fixed_{action_dir}.csv"
csv.write_text("action,status,steps,checkpoint,loss,gate\n" + f"{action},{data['status']},{data['steps']},{data['checkpoint']},{data['loss']},{data['gate']}\n", encoding="utf-8")
PY
}

cycle=0
write_status "WAITING_FOR_GPU" "initializing"
while true; do
  selected="$(choose_gpu || true)"
  if [[ -n "${selected}" ]]; then
    IFS=':' read -r GPU_ID FREE_MB GPU_UTIL SELECT_MODE <<< "${selected}"
    echo "$(date -Is) selected GPU ${GPU_ID} free ${FREE_MB} MiB util ${GPU_UTIL}% mode ${SELECT_MODE}" | tee -a "${WAIT_LOG}"
    write_status "GPU_SELECTED" "gpu=${GPU_ID},free_memory_mb=${FREE_MB},util=${GPU_UTIL},mode=${SELECT_MODE}"
    if ! train_action REMOVE remove "${GPU_ID}"; then
      echo "$(date -Is) REMOVE smoke/train failed on GPU ${GPU_ID}; will keep daemon alive and retry later" | tee -a "${WAIT_LOG}"
      write_status "TRAIN_ATTEMPT_FAILED_RETRYING" "action=REMOVE,gpu=${GPU_ID},free_memory_mb=${FREE_MB},see_log=${OUTPUT_BASE}/REMOVE_20/c14_4_gpu${GPU_ID}_rank32_smoke20/logs/train.log"
      sleep "${CHECK_INTERVAL_SECONDS}"
      cycle=$((cycle+1))
      continue
    fi
    if ! train_action REPLACE replace "${GPU_ID}"; then
      write_status "TRAIN_ATTEMPT_FAILED_RETRYING" "action=REPLACE,gpu=${GPU_ID}"
      sleep "${CHECK_INTERVAL_SECONDS}"
      cycle=$((cycle+1))
      continue
    fi
    if ! train_action TRANSLATE translate "${GPU_ID}"; then
      write_status "TRAIN_ATTEMPT_FAILED_RETRYING" "action=TRANSLATE,gpu=${GPU_ID}"
      sleep "${CHECK_INTERVAL_SECONDS}"
      cycle=$((cycle+1))
      continue
    fi
    if ! train_action ADD add "${GPU_ID}"; then
      write_status "TRAIN_ATTEMPT_FAILED_RETRYING" "action=ADD,gpu=${GPU_ID}"
      sleep "${CHECK_INTERVAL_SECONDS}"
      cycle=$((cycle+1))
      continue
    fi
    write_status "SINGLE_ACTIONS_COMPLETE" "REMOVE/REPLACE/TRANSLATE/ADD completed"
    "${PYTHON_BIN}" - "${REPORT_DIR}" <<'PY'
import json
import sys
from pathlib import Path
report_dir = Path(sys.argv[1])
actions = ["REMOVE", "REPLACE", "TRANSLATE", "ADD"]
results = {}
nonzero = 0
for action in actions:
    p = report_dir / f"c14_4_palette_fixed_{action}_20.json"
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    results[action] = data
    avg = (((data.get("eval_summary") or {}).get("avg_masked_pixel_accuracy")) or 0)
    iou = (((data.get("eval_summary") or {}).get("avg_action_specific_iou")) or 0)
    if avg > 0 or iou > 0:
        nonzero += 1
allow_mixed = nonzero >= 3
out = {
    "schema_version": "c14-4-single-action-summary-v1",
    "actions": results,
    "nonzero_actions": nonzero,
    "allow_mixed": allow_mixed,
}
(report_dir / "c14_4_single_action_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
PY
    if "${PYTHON_BIN}" - "${REPORT_DIR}" <<'PY'
import json, sys
from pathlib import Path
data = json.loads((Path(sys.argv[1]) / "c14_4_single_action_summary.json").read_text())
raise SystemExit(0 if data.get("allow_mixed") else 1)
PY
    then
      echo "$(date -Is) mixed_80 allowed by nonzero single-action metrics" | tee -a "${WAIT_LOG}"
      train_action MIXED mixed_80 "${GPU_ID}"
      write_status "COMPLETE_WITH_MIXED" "single actions and mixed completed"
    else
      echo "$(date -Is) mixed_80 skipped; fewer than 3 nonzero single-action metrics" | tee -a "${WAIT_LOG}"
      write_status "COMPLETE_SINGLE_ACTIONS_MIXED_SKIPPED" "mixed skipped by gate"
    fi
    exit 0
  fi

  nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv > "${OUTPUT_BASE}/c14_4_last_gpu_audit.csv" || true
  echo "$(date -Is) no GPU with >= ${MIN_TRY_FREE_MB} MiB free; sleeping ${CHECK_INTERVAL_SECONDS}s" | tee -a "${WAIT_LOG}"
  write_status "WAITING_FOR_GPU" "cycle=${cycle}"
  cycle=$((cycle+1))
  if [[ "${cycle}" -ge "${MAX_WAIT_CYCLES}" ]]; then
    write_status "WAIT_TIMEOUT" "max_wait_cycles=${MAX_WAIT_CYCLES}"
    exit 2
  fi
  sleep "${CHECK_INTERVAL_SECONDS}"
done
