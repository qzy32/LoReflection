#!/usr/bin/env bash
set -euo pipefail
ACTION=TRANSLATE
METADATA=/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_overfit_dataset_v1/metadata_translate.csv
OUTPUT_ROOT=/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_overfit_v1/${ACTION}
DATASET_REPEAT=${DATASET_REPEAT:-4}
NUM_EPOCHS=${NUM_EPOCHS:-1}
SAVE_STEPS=${SAVE_STEPS:-10}
SEED=${SEED:-4313}
GPU_ID=${GPU_ID:-3}
source "$(dirname "$0")/c13_train_common.sh"
