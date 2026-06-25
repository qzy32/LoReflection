#!/usr/bin/env bash
set -euo pipefail

# Server-side wait-and-run helper for C14.1.
# It is intentionally not started automatically by Codex.

PREFER_FREE_MB="${PREFER_FREE_MB:-60000}"
FALLBACK_FREE_MB="${FALLBACK_FREE_MB:-22000}"
CHECK_INTERVAL_SEC="${CHECK_INTERVAL_SEC:-300}"
LOG_PATH="${LOG_PATH:-/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/autogpu_wait.log}"
STATUS_PATH="${STATUS_PATH:-/wuqingyaoa800/qiuziyan/LoReflection/reports/c14_1_autogpu_wait_status.json}"

mkdir -p "$(dirname "${LOG_PATH}")" "$(dirname "${STATUS_PATH}")"

choose_gpu() {
  nvidia-smi --query-gpu=index,memory.free,utilization.gpu,name --format=csv,noheader,nounits |
    awk -F, -v prefer="${PREFER_FREE_MB}" -v fallback="${FALLBACK_FREE_MB}" '
      {
        gsub(/^ +| +$/, "", $1); gsub(/^ +| +$/, "", $2); gsub(/^ +| +$/, "", $3); gsub(/^ +| +$/, "", $4);
        if ($2+0 >= prefer+0) { print $1 "," $2 ",GPU_READY_80GB," $4; exit }
        if ($2+0 >= fallback+0 && best_free+0 < $2+0) { best=$1; best_free=$2; best_name=$4 }
      }
      END {
        if (best != "") print best "," best_free ",GPU_READY_24GB," best_name;
      }'
}

while true; do
  ts="$(date --iso-8601=seconds)"
  choice="$(choose_gpu || true)"
  if [[ -n "${choice}" ]]; then
    IFS=',' read -r gpu free_mb state name <<< "${choice}"
    echo "${ts} selected GPU ${gpu} (${name}) free=${free_mb} state=${state}" | tee -a "${LOG_PATH}"
    cat > "${STATUS_PATH}" <<JSON
{"updated_at":"${ts}","selected_gpu":${gpu},"free_memory_mb":${free_mb},"state":"${state}","next":"probe_remove"}
JSON
    export CUDA_VISIBLE_DEVICES="${gpu}"
    bash /wuqingyaoa800/qiuziyan/LoReflection/scripts/c14_1_autogpu_memory_probe_remove.sh
    exit $?
  fi
  echo "${ts} no GPU above fallback threshold; sleeping ${CHECK_INTERVAL_SEC}s" | tee -a "${LOG_PATH}"
  cat > "${STATUS_PATH}" <<JSON
{"updated_at":"${ts}","selected_gpu":null,"state":"GPU_BUSY","next_check_sec":${CHECK_INTERVAL_SEC}}
JSON
  sleep "${CHECK_INTERVAL_SEC}"
done
