#!/usr/bin/env bash
set -euo pipefail
REPO=/wuqingyaoa800/qiuziyan/LoReflection
DATASET=${REPO}/outputs/semantic_repair4_medium_dataset_v2_palette_fixed
LOG_ROOT=${REPO}/outputs/qwen_semantic_repair4_palette_fixed_v1
REPORT=/tmp/loreflection_c14_3_reports/c14_3_wait_status.json
PREFER_FREE_MB=${PREFER_FREE_MB:-60000}
CHECK_INTERVAL_SECONDS=${CHECK_INTERVAL_SECONDS:-300}
MAX_WAIT_CYCLES=${MAX_WAIT_CYCLES:-288}
ACTIONS=(remove replace translate add)
mkdir -p "${LOG_ROOT}"
choose_gpu() {
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | awk -F, -v min="${PREFER_FREE_MB}" '
    {gsub(/ /,"",$1); gsub(/ /,"",$2); if ($2>=min && $2>best_free) {best=$1; best_free=$2}}
    END {if (best_free>0) print best ":" best_free}'
}
cycle=0
while true; do
  selected=$(choose_gpu || true)
  ts=$(date -Is)
  if [[ -n "${selected}" ]]; then
    GPU_ID=${selected%%:*}
    FREE_MB=${selected##*:}
    echo "${ts} selected GPU ${GPU_ID} free ${FREE_MB} MiB" | tee -a "${LOG_ROOT}/c14_3_wait_and_run.log"
    cat > "${REPORT}" <<JSON
{"status":"GPU_SELECTED","timestamp":"${ts}","gpu_id":"${GPU_ID}","free_memory_mb":${FREE_MB},"threshold_mb":${PREFER_FREE_MB}}
JSON
    for action in "${ACTIONS[@]}"; do
      upper=$(echo "$action" | tr '[:lower:]' '[:upper:]')
      smoke_root="${LOG_ROOT}/${upper}_20/gpu${GPU_ID}_rank32_smoke20"
      mkdir -p "${smoke_root}/logs"
      echo "${ts} running smoke ${upper} on GPU ${GPU_ID}" | tee -a "${LOG_ROOT}/c14_3_wait_and_run.log"
      GPU_ID="${GPU_ID}" METADATA="${DATASET}/metadata_${action}.csv" OUTPUT_ROOT="${smoke_root}" DATASET_REPEAT=1 NUM_EPOCHS=1 SAVE_STEPS=20 SEED=4411 bash "${DATASET}/_scripts/c14_3_train_common.sh"
      echo "$(date -Is) running 300-step ${upper} on GPU ${GPU_ID}" | tee -a "${LOG_ROOT}/c14_3_wait_and_run.log"
      CUDA_VISIBLE_DEVICES="${GPU_ID}" bash "${DATASET}/_scripts/c14_3_train_${action}_20.sh"
    done
    cat > "${REPORT}" <<JSON
{"status":"COMPLETED_SINGLE_ACTIONS","timestamp":"$(date -Is)","gpu_id":"${GPU_ID}","actions":["REMOVE","REPLACE","TRANSLATE","ADD"]}
JSON
    exit 0
  fi
  nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv > "${LOG_ROOT}/c14_3_last_gpu_audit.csv" || true
  echo "${ts} no GPU with >= ${PREFER_FREE_MB} MiB free; sleeping ${CHECK_INTERVAL_SECONDS}s" | tee -a "${LOG_ROOT}/c14_3_wait_and_run.log"
  cat > "${REPORT}" <<JSON
{"status":"WAITING_FOR_GPU","timestamp":"${ts}","threshold_mb":${PREFER_FREE_MB},"cycle":${cycle},"max_cycles":${MAX_WAIT_CYCLES},"log":"${LOG_ROOT}/c14_3_wait_and_run.log"}
JSON
  cycle=$((cycle+1))
  if [[ "${cycle}" -ge "${MAX_WAIT_CYCLES}" ]]; then
    echo "$(date -Is) max wait cycles reached" | tee -a "${LOG_ROOT}/c14_3_wait_and_run.log"
    exit 2
  fi
  sleep "${CHECK_INTERVAL_SECONDS}"
done
