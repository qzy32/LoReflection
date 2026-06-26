# A Initial Problem Reproduction

- sample_id: `36c96aa6-a318-4212-aecc-22a206d7b217_room_00`
- Goal State contains coffee_table near dining_table: `True`
- prompt contains coffee table close/near dining table: `True`
- coffee_table to dining_table edge_gap_m: `2.3576117680012874`
- coffee_table to dining_table center_distance_m: `3.7646782508203804`
- near threshold: edge_gap_m <= 0.8 or center_distance_m <= 1.5
- architecture_control_prompt is null: `True`
- palette_control_prompt is null: `True`

## Relation validation
```json
{
  "geometry_verified": [
    {
      "subject": "dining_chair",
      "predicate": "near",
      "object": "dining_table",
      "source": "geometry_verified",
      "geometry_validation": {
        "status": "pass",
        "reason": null,
        "evidence": {
          "subject_instance_id": "furniture/102",
          "object_instance_id": "furniture/103",
          "edge_gap_m": 0.0,
          "center_distance_m": 0.766599385402832,
          "edge_gap_threshold_m": 0.6,
          "center_threshold_m": 1.5
        }
      },
      "validation_source": "layout_json",
      "prompt_allowed": true
    }
  ],
  "dropped": [
    {
      "subject": "coffee_table",
      "predicate": "near",
      "object": "dining_table",
      "source": "rule",
      "geometry_validation": {
        "status": "invalid",
        "reason": "target_geometry_not_near",
        "evidence": {
          "subject_instance_id": "furniture/108",
          "object_instance_id": "furniture/103",
          "edge_gap_m": 2.3576117680012874,
          "center_distance_m": 3.7646782508203804,
          "edge_gap_threshold_m": 0.8,
          "center_threshold_m": 1.5
        }
      },
      "validation_source": "layout_json",
      "prompt_allowed": false,
      "reason": "target_geometry_not_near"
    }
  ],
  "validation_source": "layout_json"
}
```

- relation_invalid: `coffee_table near dining_table`
