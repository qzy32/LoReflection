#!/usr/bin/env bash
set -euo pipefail
cd "${LOREFLECTION_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0}"
PYTHON_BIN="${PYTHON_BIN:-/wuqingyaoa800/qiuziyan/envs/qwen35-serve/bin/python}"
MODEL_PATH="${LLM_MODEL_PATH:-/wuqingyaoa800/chengjiajia_datas/models/Qwen2.5-7B-Instruct}"
REQUEST_JSONL="${REQUEST_JSONL:-data/loreflection_prompt_label_requests/p1_small_metric_v2_prompt_label_requests.jsonl}"
TEMPLATE_ROOT="${TEMPLATE_ROOT:-data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels}"
OUTPUT_ROOT="${OUTPUT_ROOT:-data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm}"
mkdir -p "$OUTPUT_ROOT/audits" "reports/prompt_label_generation"
"$PYTHON_BIN" scripts/qwen_arch_control/generate_llm_prompt_variants.py \
  --request-jsonl "$REQUEST_JSONL" \
  --template-root "$TEMPLATE_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --output-jsonl "$OUTPUT_ROOT/llm_prompt_outputs_full200.jsonl" \
  --failed-jsonl "$OUTPUT_ROOT/failed_requests.jsonl" \
  --model-path "$MODEL_PATH"
"$PYTHON_BIN" -m loreflection.qwen_arch_control.prompt_labels.audit_llm_prompt_outputs \
  "$OUTPUT_ROOT/llm_prompt_outputs_full200.jsonl" \
  --request-jsonl "$REQUEST_JSONL" \
  --output "$OUTPUT_ROOT/audits/llm_prompt_audit_report.json" \
  --expected-count 200
