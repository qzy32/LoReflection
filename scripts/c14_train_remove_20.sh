#!/usr/bin/env bash
set -euo pipefail

# Server-side C14 REMOVE 20-sample smoke command mirror.
# Run on A800 from /wuqingyaoa800/qiuziyan/LoReflection after selecting a GPU with enough free memory.

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-3}"
cd /wuqingyaoa800/qiuziyan/LoReflection
bash outputs/semantic_repair4_medium_dataset_v1/_scripts/c14_train_remove.sh
