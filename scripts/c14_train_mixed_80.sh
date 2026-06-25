#!/usr/bin/env bash
set -euo pipefail

# Server-side C14 MIXED_80 command mirror. Run only after single-action medium smoke gates are usable.

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-3}"
cd /wuqingyaoa800/qiuziyan/LoReflection
bash outputs/semantic_repair4_medium_dataset_v1/_scripts/c14_train_mixed_80.sh
