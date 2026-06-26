#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2}"
export P1_METRIC_V2_LORA="${P1_METRIC_V2_LORA:-$OUT/train/run/epoch-2.safetensors}"
/home/chengjiajia/anaconda3/bin/python scripts/qwen_arch_control/quantize_qwen_output_palette.py \
  --input-dir "$OUT/infer" \
  --output-dir "$OUT/quantized" \
  --report "$OUT/eval/palette_quantization_report.json"
/home/chengjiajia/anaconda3/bin/python scripts/qwen_arch_control/evaluate_p0_sanity_outputs.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --train-log "$OUT/logs/train.log" \
  --train-log "$OUT/logs/train_command.txt" \
  --script scripts/qwen_arch_control/run_p1_small_metric_v2_train.sh \
  --script scripts/qwen_arch_control/run_p1_small_metric_v2_infer.sh \
  --script scripts/qwen_arch_control/infer_qwen_arch_incontext.py \
  --checkpoint-used "$P1_METRIC_V2_LORA" \
  --phase-label p1
cp "$OUT/eval/p0_sanity_eval_report.json" "$OUT/eval/p1_small_metric_v2_eval_report.json"
/home/chengjiajia/anaconda3/bin/python scripts/qwen_arch_control/build_p0_infer_review_sheet.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA"
cp "$OUT/eval/p0_infer_review_sheet.png" "$OUT/eval/p1_small_metric_v2_review_sheet.png"
cp "$OUT/eval/p0_infer_review.html" "$OUT/eval/p1_small_metric_v2_review.html"
/home/chengjiajia/anaconda3/bin/python - <<'PY'
from pathlib import Path
import json
root=Path('/wuqingyaoa800/qiuziyan/LoReflection_arch_p0')
out=root/'outputs/qwen_arch_incontext_p1_small_metric_v2'
eval_report=json.loads((out/'eval/p1_small_metric_v2_eval_report.json').read_text())
scale=json.loads((root/'data/loreflection_qwen_arch_control_p1_small_metric_v2/audits/architecture_condition_scale_report.json').read_text())
contract=json.loads((out/'eval/inference_command_contract_check.json').read_text())
summary=out/'P1_SMALL_METRIC_V2_TRAINING_SUMMARY.md'
summary.write_text(f"""# P1-small metric_v2 Training Summary

- dataset: `{root/'data/loreflection_qwen_arch_control_p1_small_metric_v2'}`
- metadata: `{root/'data/loreflection_qwen_arch_control_p1_small_metric_v2/metadata.csv'}`
- checkpoint: `{out/'train/run/epoch-2.safetensors'}`
- route: `image + prompt + context_image`
- renderer_version: `metric_v2`
- metric_transform_exists_rate: `{scale.get('metric_transform_exists_rate')}`
- inference_ran: `{eval_report.get('inference_ran')}`
- num_infer_samples: `{eval_report.get('num_infer_samples')}`
- uses_context_image: `{contract.get('uses_context_image')}`
- uses_p1_metric_v2_lora: `{contract.get('uses_lora_checkpoint')}`
- uses_incontext_union: `{contract.get('uses_incontext_union')}`
- forbidden_inpaint_fields_present: `{eval_report.get('forbidden_inpaint_fields_present')}`
- target_pixel_agreement_after_quantization: `{eval_report.get('target_pixel_agreement_after_quantization')}`
- furniture_pixel_precision: `{eval_report.get('furniture_pixel_precision')}`
- furniture_pixel_recall: `{eval_report.get('furniture_pixel_recall')}`
- furniture_pixel_f1: `{eval_report.get('furniture_pixel_f1')}`
- palette_unknown_rate_before_quantization: `{eval_report.get('palette_unknown_rate_before_quantization')}`
- palette_unknown_rate_after_quantization: `{eval_report.get('palette_unknown_rate_after_quantization')}`
- condition_contains_furniture_rate: `{eval_report.get('condition_contains_furniture_rate')}`
- target_has_furniture_pixels_rate: `{eval_report.get('target_has_furniture_pixels_rate')}`

Decision threshold: inference must run, context route must be used, forbidden inpaint fields must be absent, palette unknown after quantization must be 0.0, target agreement must be >= 0.55, and furniture F1 must be >= 0.30.
""", encoding='utf-8')
PY
