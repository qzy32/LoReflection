#!/usr/bin/env bash
set -euo pipefail
REMOTE_REPO=${REMOTE_REPO:-/wuqingyaoa800/qiuziyan/LoReflection}
CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-${GPU_ID:-0}} bash "${REMOTE_REPO}/outputs/semantic_repair4_medium_dataset_v2_palette_fixed/_scripts/c14_3_train_translate_20.sh"
