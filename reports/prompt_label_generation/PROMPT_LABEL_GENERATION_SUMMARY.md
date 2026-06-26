# Prompt Label Generation Summary

- dataset: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels`
- llm request jsonl: `data/loreflection_prompt_label_requests/p1_small_metric_v2_prompt_label_requests.jsonl`
- num_samples: 200
- variant_count_per_sample: 3
- starts_with_context_control_rate: 1.0
- coordinate_leakage_rate: 0.0
- required_slot_coverage_rate: 1.0
- unknown_category_term_rate: 0.0
- llm_request_exported: True
- llm_actual_generation_used: False
- status: pass

## Example Prompts

### 36c96aa6-a318-4212-aecc-22a206d7b217_room_00
- template_minimal: Context_Control. Create a top-down fixed-palette semantic livingroom layout with 1 coffee table, 4 dining chairs, and 1 dining table. Follow the architecture condition image, keep furniture inside the room, and keep door and window clearance regions free.
- template_functional: Context_Control. Design a functional livingroom semantic layout with 1 coffee table, 4 dining chairs, and 1 dining table. Use the dining table as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.
- template_user_like: Context_Control. I need a practical livingroom layout with 1 coffee table, 4 dining chairs, and 1 dining table. Respect the room shape shown in the architecture image and avoid blocking doors or windows.

### 36c96aa6-a318-4212-aecc-22a206d7b217_room_01
- template_minimal: Context_Control. Create a top-down fixed-palette semantic elderlyroom layout with 2 desks. Follow the architecture condition image, keep furniture inside the room, and keep door and window clearance regions free.
- template_functional: Context_Control. Design a functional elderlyroom semantic layout with 2 desks. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.
- template_user_like: Context_Control. I need a practical elderlyroom layout with 2 desks. Respect the room shape shown in the architecture image and avoid blocking doors or windows.

### 36c96aa6-a318-4212-aecc-22a206d7b217_room_02
- template_minimal: Context_Control. Create a top-down fixed-palette semantic study layout with 1 armchair, and 1 desk. Follow the architecture condition image, keep furniture inside the room, and keep door and window clearance regions free.
- template_functional: Context_Control. Design a functional study semantic layout with 1 armchair, and 1 desk. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.
- template_user_like: Context_Control. I need a practical study layout with 1 armchair, and 1 desk. Respect the room shape shown in the architecture image and avoid blocking doors or windows.

### 36c96aa6-a318-4212-aecc-22a206d7b217_room_05
- template_minimal: Context_Control. Create a top-down fixed-palette semantic bedroom layout with 2 desks, and 1 pendant lamp. Follow the architecture condition image, keep furniture inside the room, and keep door and window clearance regions free.
- template_functional: Context_Control. Design a functional bedroom semantic layout with 2 desks, and 1 pendant lamp. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.
- template_user_like: Context_Control. I need a practical bedroom layout with 2 desks, and 1 pendant lamp. Respect the room shape shown in the architecture image and avoid blocking doors or windows.

### faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00
- template_minimal: Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling lamp, 1 desk, 1 kids bed, 1 lazy sofa, and 1 single bed. Follow the architecture condition image, keep furniture inside the room, and keep door and window clearance regions free.
- template_functional: Context_Control. Design a functional bedroom semantic layout with 1 ceiling lamp, 1 desk, 1 kids bed, 1 lazy sofa, and 1 single bed. Use the single bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.
- template_user_like: Context_Control. I need a practical bedroom layout with 1 ceiling lamp, 1 desk, 1 kids bed, 1 lazy sofa, and 1 single bed. Respect the room shape shown in the architecture image and avoid blocking doors or windows.

## Rich Goal LoState Examples

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "36c96aa6-a318-4212-aecc-22a206d7b217_room_00",
  "room_type": "livingroom",
  "furniture_slots": [
    {
      "slot_id": "slot_coffee_table",
      "category": "coffee_table",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_dining_chair",
      "category": "dining_chair",
      "required": true,
      "count": 4
    },
    {
      "slot_id": "slot_dining_table",
      "category": "dining_table",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "coffee_table": 1,
    "dining_chair": 4,
    "dining_table": 1
  },
  "pairwise_constraints": [
    {
      "subject": "dining_chair",
      "predicate": "near",
      "object": "dining_table",
      "source": "rule"
    },
    {
      "subject": "coffee_table",
      "predicate": "near",
      "object": "dining_table",
      "source": "rule"
    }
  ],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image",
    "door_clearance_free"
  ],
  "architecture_condition_ref": "meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_00_architecture.json"
}
```

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "36c96aa6-a318-4212-aecc-22a206d7b217_room_01",
  "room_type": "elderlyroom",
  "furniture_slots": [
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 2
    }
  ],
  "required_counts": {
    "desk": 2
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image"
  ],
  "architecture_condition_ref": "meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_architecture.json"
}
```

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "36c96aa6-a318-4212-aecc-22a206d7b217_room_02",
  "room_type": "study",
  "furniture_slots": [
    {
      "slot_id": "slot_armchair",
      "category": "armchair",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "armchair": 1,
    "desk": 1
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image"
  ],
  "architecture_condition_ref": "meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_02_architecture.json"
}
```
