# Prompt Construction Trace

```text
3D-FRONT / metric_v2 layout JSON
  -> scene_fact_extractor.py
  -> scene_facts
  -> goal_constraint_extractor.py
  -> Goal LoState rich
  -> template_prompt_generator.py or llm_prompt_request_exporter.py
  -> Qwen2.5-7B-Instruct prompt generation
  -> metadata_llm_functional.csv / metadata_mixed_llm_variants.csv
  -> DiffSynth-Studio Qwen-Image In-Context-Control-Union training
```

Goal-aligned v2:

```text
layout geometry
  -> relation_triplet_extractor.py
  -> placement_order_planner.py
  -> goal_aligned_llm_request_builder.py
  -> Qwen2.5-7B-Instruct or deterministic fallback
  -> metadata_goal_aligned_relation_rich.csv
```

## Code Files
- `loreflection/qwen_arch_control/prompt_labels/scene_fact_extractor.py`: exists
- `loreflection/qwen_arch_control/prompt_labels/goal_constraint_extractor.py`: exists
- `loreflection/qwen_arch_control/prompt_labels/template_prompt_generator.py`: exists
- `loreflection/qwen_arch_control/prompt_labels/llm_prompt_request_exporter.py`: exists
- `loreflection/qwen_arch_control/prompt_labels/generate_llm_prompt_variants.py`: MISSING
- `loreflection/qwen_arch_control/prompt_labels/relation_triplet_extractor.py`: exists
- `loreflection/qwen_arch_control/prompt_labels/placement_order_planner.py`: exists
- `loreflection/qwen_arch_control/prompt_labels/goal_aligned_llm_request_builder.py`: exists
- `loreflection/qwen_arch_control/prompt_labels/generate_goal_aligned_llm_prompts.py`: exists
