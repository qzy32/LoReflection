# Goal LoState Examples

Goal LoState should contain room type, furniture slots, required counts, constraints, and architecture refs. It should not contain geometry/provenance fields such as `center_m`, `size_m`, `orientation_deg`, `bbox_px`, `footprint_m`, `source_json_path`, or `metric_transform`.

## 1. 36c96aa6-a318-4212-aecc-22a206d7b217_room_00

- room_type: `livingroom`
- contains_geometry_fields: `[]`

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

## 2. 36c96aa6-a318-4212-aecc-22a206d7b217_room_01

- room_type: `elderlyroom`
- contains_geometry_fields: `[]`

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

## 3. 36c96aa6-a318-4212-aecc-22a206d7b217_room_02

- room_type: `study`
- contains_geometry_fields: `[]`

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

## 4. 36c96aa6-a318-4212-aecc-22a206d7b217_room_05

- room_type: `bedroom`
- contains_geometry_fields: `[]`

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "36c96aa6-a318-4212-aecc-22a206d7b217_room_05",
  "room_type": "bedroom",
  "furniture_slots": [
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 2
    },
    {
      "slot_id": "slot_pendant_lamp",
      "category": "pendant_lamp",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "desk": 2,
    "pendant_lamp": 1
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image"
  ],
  "architecture_condition_ref": "meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_architecture.json"
}
```

## 5. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00

- room_type: `bedroom`
- contains_geometry_fields: `[]`

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00",
  "room_type": "bedroom",
  "furniture_slots": [
    {
      "slot_id": "slot_ceiling_lamp",
      "category": "ceiling_lamp",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_kids_bed",
      "category": "kids_bed",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_lazy_sofa",
      "category": "lazy_sofa",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_single_bed",
      "category": "single_bed",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "ceiling_lamp": 1,
    "desk": 1,
    "kids_bed": 1,
    "lazy_sofa": 1,
    "single_bed": 1
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image",
    "window_clearance_free"
  ],
  "architecture_condition_ref": "meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_architecture.json"
}
```

## 6. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01

- room_type: `bedroom`
- contains_geometry_fields: `[]`

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01",
  "room_type": "bedroom",
  "furniture_slots": [
    {
      "slot_id": "slot_ceiling_lamp",
      "category": "ceiling_lamp",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 2
    },
    {
      "slot_id": "slot_kids_bed",
      "category": "kids_bed",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_lounge_chair",
      "category": "lounge_chair",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "ceiling_lamp": 1,
    "desk": 2,
    "kids_bed": 1,
    "lounge_chair": 1
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image",
    "window_clearance_free"
  ],
  "architecture_condition_ref": "meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_architecture.json"
}
```

## 7. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_02

- room_type: `courtyard`
- contains_geometry_fields: `[]`

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "faf62fbc-739a-40da-aac3-12b6807ee7e3_room_02",
  "room_type": "courtyard",
  "furniture_slots": [
    {
      "slot_id": "slot_corner_side_table",
      "category": "corner_side_table",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_lounge_chair",
      "category": "lounge_chair",
      "required": true,
      "count": 2
    },
    {
      "slot_id": "slot_pendant_lamp",
      "category": "pendant_lamp",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "corner_side_table": 1,
    "desk": 1,
    "lounge_chair": 2,
    "pendant_lamp": 1
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image",
    "door_clearance_free",
    "window_clearance_free"
  ],
  "architecture_condition_ref": "meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_02_architecture.json"
}
```

## 8. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05

- room_type: `livingroom`
- contains_geometry_fields: `[]`

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05",
  "room_type": "livingroom",
  "furniture_slots": [
    {
      "slot_id": "slot_ceiling_lamp",
      "category": "ceiling_lamp",
      "required": true,
      "count": 2
    },
    {
      "slot_id": "slot_coffee_table",
      "category": "coffee_table",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_lazy_sofa",
      "category": "lazy_sofa",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_multi_seat_sofa",
      "category": "multi_seat_sofa",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_table",
      "category": "table",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_tv_stand",
      "category": "tv_stand",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "ceiling_lamp": 2,
    "coffee_table": 1,
    "desk": 1,
    "lazy_sofa": 1,
    "multi_seat_sofa": 1,
    "table": 1,
    "tv_stand": 1
  },
  "pairwise_constraints": [
    {
      "subject": "tv_stand",
      "predicate": "near",
      "object": "multi_seat_sofa",
      "source": "rule"
    },
    {
      "subject": "coffee_table",
      "predicate": "near",
      "object": "multi_seat_sofa",
      "source": "rule"
    }
  ],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image",
    "door_clearance_free",
    "window_clearance_free"
  ],
  "architecture_condition_ref": "meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05_architecture.json"
}
```

## 9. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_08

- room_type: `bedroom`
- contains_geometry_fields: `[]`

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "faf62fbc-739a-40da-aac3-12b6807ee7e3_room_08",
  "room_type": "bedroom",
  "furniture_slots": [
    {
      "slot_id": "slot_ceiling_lamp",
      "category": "ceiling_lamp",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 3
    },
    {
      "slot_id": "slot_double_bed",
      "category": "double_bed",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "ceiling_lamp": 1,
    "desk": 3,
    "double_bed": 1
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image",
    "window_clearance_free"
  ],
  "architecture_condition_ref": "meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_08_architecture.json"
}
```

## 10. 23a5fa77-0aa5-45f4-8399-3265005b1def_room_00

- room_type: `bedroom`
- contains_geometry_fields: `[]`

```json
{
  "schema_version": "goal-lostate-rich-v1",
  "state_role": "goal",
  "sample_id": "23a5fa77-0aa5-45f4-8399-3265005b1def_room_00",
  "room_type": "bedroom",
  "furniture_slots": [
    {
      "slot_id": "slot_desk",
      "category": "desk",
      "required": true,
      "count": 3
    },
    {
      "slot_id": "slot_double_bed",
      "category": "double_bed",
      "required": true,
      "count": 1
    },
    {
      "slot_id": "slot_pendant_lamp",
      "category": "pendant_lamp",
      "required": true,
      "count": 1
    }
  ],
  "required_counts": {
    "desk": 3,
    "double_bed": 1,
    "pendant_lamp": 1
  },
  "pairwise_constraints": [],
  "global_constraints": [
    "inside_room",
    "avoid_overlap",
    "palette_exact",
    "use_architecture_condition_image",
    "window_clearance_free"
  ],
  "architecture_condition_ref": "meta/23a5fa77-0aa5-45f4-8399-3265005b1def_room_00_architecture.json"
}
```

## Current Weaknesses

- `pairwise_constraints` are mostly rule-derived and are not always true geometric relations.
- relation-rich v2 extracts triplets from layout geometry, but the generated prompt dataset used many fallback prompts.
- Goal-aligned data should be treated as relation-rich compiled prompt data unless direct LLM success rate improves.
