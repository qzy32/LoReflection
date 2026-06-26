# P1-small Training And Evaluation Summary

## Inputs

- Dataset: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small`
- Metadata: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small/metadata.csv`
- Checkpoint: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/train/run/epoch-2.safetensors`
- Route: `image + prompt + context_image`
- LoRA family: `Qwen-Image-In-Context-Control-Union`

## Outputs

- Raw inference: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/infer`
- Quantized inference: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/quantized`
- Eval report: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/eval/p1_small_eval_report.json`
- Palette report: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/eval/palette_quantization_report.json`
- Inference contract: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/eval/inference_command_contract_check.json`
- Training contract: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/eval/training_command_contract_check.json`
- Review sheet PNG: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/eval/p1_small_review_sheet.png`
- Review HTML: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small/eval/p1_small_review.html`

## Metrics

- inference_ran: `True`
- num_infer_samples: `20`
- training_command_uses_context_image: `True`
- uses_context_image: `True`
- uses_p1_lora: `True`
- uses_incontext_union: `True`
- forbidden_inpaint_fields_present: `False`
- dataset_is_real_3dfront: `True`
- target_pixel_agreement_after_quantization: `0.6281181335449219`
- furniture_pixel_precision: `0.3663631618627849`
- furniture_pixel_recall: `0.6004486350847844`
- furniture_pixel_f1: `0.45506738991060297`
- palette_unknown_rate_before_quantization: `0.42547454833984377`
- palette_unknown_rate_after_quantization: `0.0`
- condition_contains_furniture_rate: `0.0`
- target_has_furniture_pixels_rate: `1.0`
- condition_target_separation_ok: `True`

## Decision

- p1_small_baseline_pass: `True`
- threshold: target agreement >= 0.55 and furniture F1 >= 0.30, with context route and no forbidden inpaint fields.
