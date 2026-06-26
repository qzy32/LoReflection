# P1-small Architecture Condition Scale Audit Summary

- dataset_root: `data/loreflection_qwen_arch_control_p1_small`
- num_samples: 200
- architecture_source_of_truth: raw_3dfront_json
- qwen_generates_architecture: False
- qwen_generates_furniture_only: True
- requires_inverse_transform_for_furniture: True
- source_scene_json_exists_rate: 1.0
- polygon_m_exists_rate: 1.0
- polygon_px_exists_rate: 1.0
- layout_metric_fields_rate: 1.0
- metric_transform_exists_rate: 0.0
- implicit_transform_recoverable_rate: 1.0
- implicit_transform_recoverable: True
- normalized_v1_scale_risk: True
- metric_v2_recommended: True
- room_type_unknown_rate: 0.0
- bbox_boundary_fallback_rate: 0.0
- boundary_source_distribution: `{'unknown': 200}`
- recommendation: add explicit metric_transform before P1-1000

Interpretation: P1-small is valid as a normalized_v1 baseline. Before P1-1000 or P2, add explicit metric transforms or migrate to metric_v2 rendering so absolute room scale is represented in the condition/target pair and inverse furniture parsing is contract-level rather than fallback-level.
