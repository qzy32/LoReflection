# P0 Inference Evaluation Summary

## Inputs

- Checkpoint: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/train_p0_50/run/epoch-2.safetensors`
- Metadata: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_real_p0/metadata.csv`
- Inference wrapper: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/scripts/qwen_arch_control/infer_qwen_arch_incontext.py`
- Shell wrapper: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/scripts/qwen_arch_control/run_p0_sanity_infer.sh`

## Outputs

- Raw outputs: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/infer`
- Quantized outputs: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/quantized`
- Review sheet PNG: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/eval/p0_infer_review_sheet.png`
- Review sheet HTML: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/eval/p0_infer_review.html`
- Eval report: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/eval/p0_sanity_eval_report.json`
- Palette report: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/eval/palette_quantization_report.json`
- Inference contract: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p0_sanity/eval/inference_command_contract_check.json`

## Metrics

- num infer samples: `10`
- inference_ran: `True`
- training_command_uses_context_image: `True`
- target_pixel_agreement_after_quantization: `0.72047119140625`
- furniture_pixel_precision: `0.3991108651210955`
- furniture_pixel_recall: `0.3976412619070913`
- furniture_pixel_f1: `0.3983747081781405`
- palette_unknown_rate_before_quantization: `0.38787078857421875`
- palette_unknown_rate_after_quantization: `0.0`
- mean_palette_distance: `3.5598202109336854`
- max_palette_distance: `111.97321319580078`
- uses_context_image: `True`
- uses_p0_lora: `True`
- uses_incontext_union: `True`
- forbidden_inpaint_fields_present: `False`

## Decision

- overfit_success: `True`
- failure_reason: `None`

## Next Recommendation

P0 overfit sanity passed under the conservative target-agreement threshold. Inspect the review sheet, then proceed to P1 200-1000 real samples if the visuals are acceptable.
