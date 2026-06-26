# LLM Prompt Generation Summary

## Model

- model_path: `/wuqingyaoa800/chengjiajia_datas/models/Qwen2.5-7B-Instruct`
- actual_llm_generation_used: true
- qwen3_5_122b_attempted: false
- vl_model_used: false

## Inputs

- request_jsonl: `data/loreflection_prompt_label_requests/p1_small_metric_v2_prompt_label_requests.jsonl`
- template_source_root: `data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels/`

## Outputs

- output_root: `data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm/`
- pilot20_jsonl: `data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm/llm_prompt_outputs_pilot20.jsonl`
- full200_jsonl: `data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm/llm_prompt_outputs_full200.jsonl`
- metadata_llm_functional: `data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm/metadata_llm_functional.csv`
- metadata_mixed_llm_variants: `data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels_llm/metadata_mixed_llm_variants.csv`

## Audit

```json
{
  "num_samples": 200,
  "json_parse_success_rate": 1.0,
  "starts_with_context_control_rate": 1.0,
  "coordinate_leakage_rate": 0.0,
  "required_slot_coverage_rate": 1.0,
  "unknown_category_term_rate": 0.0,
  "invented_category_rate": 0.0,
  "empty_prompt_rate": 0.0,
  "duplicate_prompt_rate": 0.0,
  "llm_actual_generation_used": true,
  "expected_count": 200,
  "count_matches_expected": true,
  "status": "pass"
}
```

## Decision

The full200 LLM prompt dataset passes the current contract checks. It is ready for a P1-small metric_v2 + metadata_llm_functional.csv training comparison, but no training was run in this step.
