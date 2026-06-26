# P1-small metric_v2 Training Summary

- dataset: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small_metric_v2`
- metadata: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small_metric_v2/metadata.csv`
- checkpoint: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_small_metric_v2/train/run/epoch-2.safetensors`
- route: `image + prompt + context_image`
- renderer_version: `metric_v2`
- metric_transform_exists_rate: `1.0`
- inference_ran: `True`
- num_infer_samples: `20`
- uses_context_image: `True`
- uses_p1_metric_v2_lora: `True`
- uses_incontext_union: `True`
- forbidden_inpaint_fields_present: `False`
- target_pixel_agreement_after_quantization: `0.7908599853515625`
- furniture_pixel_precision: `0.28292324104491695`
- furniture_pixel_recall: `0.6430866196874864`
- furniture_pixel_f1: `0.39296374354091557`
- palette_unknown_rate_before_quantization: `0.219622802734375`
- palette_unknown_rate_after_quantization: `0.0`
- condition_contains_furniture_rate: `0.0`
- target_has_furniture_pixels_rate: `1.0`

Decision threshold: inference must run, context route must be used, forbidden inpaint fields must be absent, palette unknown after quantization must be 0.0, target agreement must be >= 0.55, and furniture F1 must be >= 0.30.


## Augmented metric_v2 contract fields

- uses_metric_transform: True
- renderer_version: metric_v2
- metric_transform_exists_rate: 1.0
- uses_p1_metric_v2_lora: True
