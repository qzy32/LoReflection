#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export PYTHON_BIN="${PYTHON_BIN:-/wuqingyaoa800/qiuziyan/envs/qwen35-serve/bin/python}"
export DATASET_ROOT="${DATASET_ROOT:-$ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm}"
export METADATA="${METADATA:-$DATASET_ROOT/metadata_mixed_llm_variants.csv}"
export OUT="${OUT:-$ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_mixed_llm}"
export P1_METRIC_V2_LORA="${P1_METRIC_V2_LORA:-$OUT/train/run/epoch-2.safetensors}"
mkdir -p "$OUT/eval" reports/prompt_label_generation reports/p1_small_metric_v2_mixed_llm_summary
"$PYTHON_BIN" scripts/qwen_arch_control/quantize_qwen_output_palette.py \
  --input-dir "$OUT/infer" \
  --output-dir "$OUT/quantized" \
  --report "$OUT/eval/palette_quantization_report.json"
"$PYTHON_BIN" scripts/qwen_arch_control/evaluate_p0_sanity_outputs.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --train-log "$OUT/logs/train.log" \
  --train-log "$OUT/logs/train_command.txt" \
  --script scripts/qwen_arch_control/run_p1_small_metric_v2_mixed_llm_train.sh \
  --script scripts/qwen_arch_control/run_p1_small_metric_v2_mixed_llm_infer.sh \
  --script scripts/qwen_arch_control/infer_qwen_arch_incontext.py \
  --checkpoint-used "$P1_METRIC_V2_LORA" \
  --phase-label p1
cp "$OUT/eval/p0_sanity_eval_report.json" "$OUT/eval/mixed_llm_eval_report.json"
"$PYTHON_BIN" scripts/qwen_arch_control/build_p0_infer_review_sheet.py \
  --output-root "$OUT" \
  --dataset-base "$DATASET_ROOT" \
  --metadata "$METADATA"
cp "$OUT/eval/p0_infer_review_sheet.png" "$OUT/eval/mixed_llm_review_sheet.png"
cp "$OUT/eval/p0_infer_review.html" "$OUT/eval/mixed_llm_review.html"
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import json, shutil
root=Path('/wuqingyaoa800/qiuziyan/LoReflection_arch_p0')
out=root/'outputs/qwen_arch_incontext_p1_small_metric_v2_mixed_llm'
basic_path=root/'outputs/qwen_arch_incontext_p1_small_metric_v2/eval/p1_small_metric_v2_eval_report.json'
llm_path=out/'eval/mixed_llm_eval_report.json'
scale_path=root/'data/loreflection_qwen_arch_control_p1_small_metric_v2/audits/architecture_condition_scale_report.json'
contract_path=out/'eval/inference_command_contract_check.json'
basic=json.loads(basic_path.read_text())
llm=json.loads(llm_path.read_text())
scale=json.loads(scale_path.read_text()) if scale_path.exists() else {}
contract=json.loads(contract_path.read_text()) if contract_path.exists() else {}
llm.update({
  'experiment_name':'p1_small_metric_v2_mixed_llm',
  'prompt_source':'qwen2_5_7b_mixed_llm_variants',
  'metadata':'metadata_mixed_llm_variants.csv',
  'uses_context_image': bool(llm.get('training_command_uses_context_image') or contract.get('uses_context_image')),
  'uses_metric_transform': scale.get('metric_transform_exists_rate') == 1.0,
  'uses_incontext_union': bool(contract.get('uses_incontext_union', True)),
  'renderer_version': 'metric_v2',
  'metric_transform_exists_rate': scale.get('metric_transform_exists_rate'),
})
llm_path.write_text(json.dumps(llm, ensure_ascii=False, indent=2)+'\n')
rows=[]
for key in ['target_pixel_agreement_after_quantization','furniture_pixel_precision','furniture_pixel_recall','furniture_pixel_f1','palette_unknown_rate_after_quantization']:
    b=basic.get(key); l=llm.get(key)
    rows.append({'metric':key,'basic_metric_v2':b,'mixed_llm':l,'delta':None if b is None or l is None else l-b})
comparison={'basic_report':str(basic_path),'mixed_llm_report':str(llm_path),'metrics':rows}
f1_delta=next(r['delta'] for r in rows if r['metric']=='furniture_pixel_f1')
tag_delta=next(r['delta'] for r in rows if r['metric']=='target_pixel_agreement_after_quantization')
comparison['decision']='llm_prompt_does_not_break_training' if llm.get('furniture_pixel_f1',0) >= basic.get('furniture_pixel_f1',0)-0.02 and llm.get('target_pixel_agreement_after_quantization',0) >= basic.get('target_pixel_agreement_after_quantization',0)-0.03 else 'llm_prompt_regression_review_needed'
(root/'reports/prompt_label_generation/mixed_llm_training_comparison.json').write_text(json.dumps(comparison, ensure_ascii=False, indent=2)+'\n')
md=['# Mixed LLM Training Comparison','','| metric | basic_metric_v2 | mixed_llm | delta |','|---|---:|---:|---:|']
for r in rows:
    md.append(f"| {r['metric']} | {r['basic_metric_v2']} | {r['mixed_llm']} | {r['delta']} |")
md += ['',f"decision: `{comparison['decision']}`",'', 'No P1-1000 was run.']
(root/'reports/prompt_label_generation/MIXED_LLM_TRAINING_COMPARISON.md').write_text('\n'.join(md)+'\n')
summary=(root/'reports/p1_small_metric_v2_mixed_llm_summary')
summary.mkdir(parents=True, exist_ok=True)
for src,name in [(llm_path,'mixed_llm_eval_report.json'),(out/'eval/palette_quantization_report.json','palette_quantization_report.json'),(contract_path,'inference_command_contract_check.json')]:
    if src.exists(): shutil.copy2(src, summary/name)
summary_md=f"""# P1-small metric_v2 Mixed LLM Training Summary

- experiment_name: `p1_small_metric_v2_mixed_llm`
- prompt_source: `qwen2_5_7b_mixed_llm_variants`
- dataset: `{root/'data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm'}`
- metadata: `metadata_mixed_llm_variants.csv`
- init_lora: `{root/'outputs/qwen_arch_incontext_p1_small_metric_v2/train/run/epoch-2.safetensors'}`
- checkpoint: `{out/'train/run/epoch-2.safetensors'}`
- inference_ran: `{llm.get('inference_ran')}`
- num_infer_samples: `{llm.get('num_infer_samples')}`
- uses_context_image: `{llm.get('uses_context_image')}`
- uses_metric_transform: `{llm.get('uses_metric_transform')}`
- uses_incontext_union: `{llm.get('uses_incontext_union')}`
- forbidden_inpaint_fields_present: `{llm.get('forbidden_inpaint_fields_present')}`
- renderer_version: `{llm.get('renderer_version')}`
- metric_transform_exists_rate: `{llm.get('metric_transform_exists_rate')}`
- target_pixel_agreement_after_quantization: `{llm.get('target_pixel_agreement_after_quantization')}`
- furniture_pixel_precision: `{llm.get('furniture_pixel_precision')}`
- furniture_pixel_recall: `{llm.get('furniture_pixel_recall')}`
- furniture_pixel_f1: `{llm.get('furniture_pixel_f1')}`
- palette_unknown_rate_after_quantization: `{llm.get('palette_unknown_rate_after_quantization')}`
- comparison_decision: `{comparison['decision']}`
"""
(summary/'MIXED_LLM_TRAINING_SUMMARY.md').write_text(summary_md)
PY
