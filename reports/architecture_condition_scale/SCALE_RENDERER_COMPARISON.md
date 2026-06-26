# Scale Renderer Comparison

## Contract

Raw 3D-FRONT scene JSON remains the architecture and metric-scale source of truth. Qwen does not generate architecture. Qwen generates furniture semantic image pixels only. Final layout is original architecture plus parsed Qwen furniture components, inverse-transformed through `architecture.metric_transform`.

## Compared Packages

- normalized_v1: `data/qwen_arch_condition_compare/normalized_v1/`
- metric_v2: `data/qwen_arch_condition_compare/metric_v2/`
- P1-small metric_v2: `data/loreflection_qwen_arch_control_p1_small_metric_v2/`

## 50-sample Comparison

| metric | normalized_v1 | metric_v2 |
| --- | ---: | ---: |
| samples | 50 | 50 |
| metric_transform_exists_rate | 0.0 | 1.0 |
| roundtrip_error_p95_m | None | 0.019740377402673762 |
| area_consistency_error_p95 | None | 0.014922273150126165 |
| target_bbox_fallback_rate | 1.0 | 0.0 |
| condition_contains_furniture_rate | 0.0 | 0.0 |
| target_has_furniture_pixels_rate | 1.0 | 1.0 |
| floor_bbox_area_px_variation | 0.6025641025641025 | 0.9229813664596274 |
| room_bbox_area_m_variation | 0.9669204699024299 | 0.9669204699024299 |
| normalized_v1_scale_risk | True | False |
| metric_v2_recommended | True | False |
| scale audit status | fail | pass |

## P1-small metric_v2 Audit

- dataset: `data/loreflection_qwen_arch_control_p1_small_metric_v2/`
- samples: 200
- metric_transform_exists_rate: 1.0
- roundtrip_error_p95_m: 0.01956249497439548
- area_consistency_error_p95: 0.014661426519215742
- target_bbox_fallback_rate: 0.0
- condition_contains_furniture_rate: 0.0
- target_has_furniture_pixels_rate: 1.0
- renderer_version: metric_v2
- training_ready: True
- build status: pass
- scale audit status: pass

## Interpretation

normalized_v1 is useful as a baseline, but it has no explicit metric transform and therefore relies on polygon bbox fallback for inverse parsing. metric_v2 stores `architecture.metric_transform` explicitly and uses the same transform for condition rendering, target rendering, and furniture inverse parsing.

metric_v2 should become the default for P1/P2. Do not use Qwen output to replace Architecture JSON; parse only furniture connected components and merge them with raw 3D-FRONT-derived architecture.
