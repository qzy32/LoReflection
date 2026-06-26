#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=${REPO_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0}
cd "$REPO_ROOT"

DATASET_BASE=${DATASET_BASE:-$REPO_ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm}
METADATA=${METADATA:-$DATASET_BASE/metadata_llm_functional.csv}
OUTPUT_ROOT=${OUTPUT_ROOT:-$REPO_ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional}
REPORT_ROOT=${REPORT_ROOT:-$REPO_ROOT/reports/palette_metric_contract_audit}
PYTHON_BIN=${PYTHON_BIN:-/wuqingyaoa800/qiuziyan/envs/qwen35-serve/bin/python}

mkdir -p "$REPORT_ROOT"

"$PYTHON_BIN" scripts/qwen_arch_control/build_palette_metric_contract_review_package.py \
  --dataset-base "$DATASET_BASE" \
  --metadata "$METADATA" \
  --output-root "$OUTPUT_ROOT" \
  --report-root "$REPORT_ROOT"

tar -czf "$REPO_ROOT/reports/palette_metric_contract_audit_package.tar.gz" -C "$REPO_ROOT/reports" palette_metric_contract_audit

if command -v zip >/dev/null 2>&1; then
  (cd "$REPO_ROOT/reports" && zip -qr palette_metric_contract_audit_package.zip palette_metric_contract_audit)
fi

echo "$REPORT_ROOT"
echo "$REPO_ROOT/reports/palette_metric_contract_audit_package.tar.gz"
