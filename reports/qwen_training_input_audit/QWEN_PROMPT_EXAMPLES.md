# Qwen Prompt Examples

## 1. 36c96aa6-a318-4212-aecc-22a206d7b217_room_01 (basic_metric_v2)

- room_type: `elderlyroom`
- furniture_counts: `{'desk': 2}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_goal_lostate.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic elderlyroom layout. Use the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions. Required furniture: 2 required desk for required_furniture. Layout guidance: Include the required desk. Keep all furniture inside the room. Avoid furniture overlap. Use only the frozen semantic palette. Keep all architectural clearance and non-placeable regions free. Use only frozen semantic categories and the frozen palette.
```

## 2. 36c96aa6-a318-4212-aecc-22a206d7b217_room_05 (basic_metric_v2)

- room_type: `bedroom`
- furniture_counts: `{'desk': 2, 'pendant_lamp': 1}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_goal_lostate.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout. Use the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions. Required furniture: 2 required desk for required_furniture, 1 required pendant_lamp for required_furniture. Layout guidance: Include the required desk. Include the required pendant_lamp. Keep all furniture inside the room. Avoid furniture overlap. Use only the frozen semantic palette. Keep all architectural clearance and non-placeable regions free. Use only frozen semantic categories and the frozen palette.
```

## 3. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00 (basic_metric_v2)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 1, 'kids_bed': 1, 'lazy_sofa': 1, 'single_bed': 1}`
- image: `target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_target_semantic.png`
- context_image: `cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_goal_lostate.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout. Use the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions. Required furniture: 1 required ceiling_lamp for required_furniture, 1 required desk for required_furniture, 1 required kids_bed for required_furniture, 1 required lazy_sofa for required_furniture, 1 required single_bed for required_furniture. Layout guidance: Include the required ceiling_lamp. Include the required desk. Include the required kids_bed. Include the required lazy_sofa. Include the required single_bed. Keep all furniture inside the room. Avoid furniture overlap. Use only the frozen semantic palette. Keep the window clearance area free. Keep all architectural clearance and non-placeable regions free. Use only frozen semantic categories and the frozen palette.
```

## 4. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01 (basic_metric_v2)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 2, 'kids_bed': 1, 'lounge_chair': 1}`
- image: `target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_target_semantic.png`
- context_image: `cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_goal_lostate.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout. Use the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions. Required furniture: 1 required ceiling_lamp for required_furniture, 2 required desk for required_furniture, 1 required kids_bed for required_furniture, 1 required lounge_chair for required_furniture. Layout guidance: Include the required ceiling_lamp. Include the required desk. Include the required kids_bed. Include the required lounge_chair. Keep all furniture inside the room. Avoid furniture overlap. Use only the frozen semantic palette. Keep the window clearance area free. Keep all architectural clearance and non-placeable regions free. Use only frozen semantic categories and the frozen palette.
```

## 5. 36c96aa6-a318-4212-aecc-22a206d7b217_room_01 (llm_functional)

- room_type: `elderlyroom`
- furniture_counts: `{'desk': 2}`
- image: `../loreflection_qwen_arch_control_p1_small_metric_v2/target/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_target_semantic.png`
- context_image: `../loreflection_qwen_arch_control_p1_small_metric_v2/cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_llm_functional_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Arrange 2 desks within the room, maintaining the requirement that they remain inside the room boundaries and avoid overlapping each other. Adhere to the specific color palette designated for an elderlyroom.
```

## 6. 36c96aa6-a318-4212-aecc-22a206d7b217_room_05 (llm_functional)

- room_type: `bedroom`
- furniture_counts: `{'desk': 2, 'pendant_lamp': 1}`
- image: `../loreflection_qwen_arch_control_p1_small_metric_v2/target/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_target_semantic.png`
- context_image: `../loreflection_qwen_arch_control_p1_small_metric_v2/cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_llm_functional_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Arrange two desks and one pendant lamp within the bedroom space, making sure there is no overlap and that all items remain within the room boundaries.
```

## 7. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00 (llm_functional)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 1, 'kids_bed': 1, 'lazy_sofa': 1, 'single_bed': 1}`
- image: `../loreflection_qwen_arch_control_p1_small_metric_v2/target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_target_semantic.png`
- context_image: `../loreflection_qwen_arch_control_p1_small_metric_v2/cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_goal_lostate_rich.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_llm_functional_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Arrange the following furniture in the bedroom: 1 ceiling lamp, 1 desk, 1 kids bed, 1 lazy sofa, and 1 single bed. Avoid overlapping and follow the architectural constraints provided.
```

## 8. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01 (llm_functional)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 2, 'kids_bed': 1, 'lounge_chair': 1}`
- image: `../loreflection_qwen_arch_control_p1_small_metric_v2/target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_target_semantic.png`
- context_image: `../loreflection_qwen_arch_control_p1_small_metric_v2/cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_goal_lostate_rich.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_llm_functional_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Arrange 1 ceiling lamp, 2 desks, 1 kids bed, and 1 lounge chair within the bedroom. Avoid overlapping and ensure all furniture is positioned inside the room. Use the architectural conditions to guide placement.
```

## 9. 36c96aa6-a318-4212-aecc-22a206d7b217_room_01 (mixed_llm)

- room_type: `elderlyroom`
- furniture_counts: `{'desk': 2}`
- image: `../loreflection_qwen_arch_control_p1_small_metric_v2/target/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_target_semantic.png`
- context_image: `../loreflection_qwen_arch_control_p1_small_metric_v2/cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_llm_short_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Place 2 desks in the room, ensuring they are inside the room and do not overlap. Use the exact palette provided for the elderlyroom type.
```

## 10. 36c96aa6-a318-4212-aecc-22a206d7b217_room_05 (mixed_llm)

- room_type: `bedroom`
- furniture_counts: `{'desk': 2, 'pendant_lamp': 1}`
- image: `../loreflection_qwen_arch_control_p1_small_metric_v2/target/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_target_semantic.png`
- context_image: `../loreflection_qwen_arch_control_p1_small_metric_v2/cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_llm_short_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Place two desks and one pendant lamp in the bedroom, ensuring they do not overlap and are inside the room bounds.
```

## 11. 36c96aa6-a318-4212-aecc-22a206d7b217_room_01 (goal_aligned_functional)

- room_type: `elderlyroom`
- furniture_counts: `{'desk': 2}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Place two desks in the elderlyroom ensuring they are inside the room, avoid overlapping, use the exact palette, and adhere to architectural conditions.
```

prompt_llm_functional:

```text
Context_Control. Place two desks in the elderlyroom ensuring they are inside the room, avoid overlapping, use the exact palette, and adhere to architectural conditions.
```

prompt_llm_relation_rich:

```text
Context_Control. Place two desks in the elderlyroom such that they are inside the room, do not overlap, use the exact palette, and follow architectural conditions.
```

## 12. 36c96aa6-a318-4212-aecc-22a206d7b217_room_05 (goal_aligned_functional)

- room_type: `bedroom`
- furniture_counts: `{'desk': 2, 'pendant_lamp': 1}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 2 desk, 1 pendant_lamp. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_functional:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 2 desk, 1 pendant_lamp. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_relation_rich:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 2 desk, 1 pendant_lamp. Place the desk as the main anchor, then arrange pendant_lamp; keep pendant_lamp paired_with desk. Respect these layout relations: pendant_lamp paired_with desk. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

## 13. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00 (goal_aligned_functional)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 1, 'kids_bed': 1, 'lazy_sofa': 1, 'single_bed': 1}`
- image: `target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_target_semantic.png`
- context_image: `cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_goal_lostate_rich.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 1 desk, 1 kids_bed, 1 lazy_sofa, 1 single_bed. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_functional:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 1 desk, 1 kids_bed, 1 lazy_sofa, 1 single_bed. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_relation_rich:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 1 desk, 1 kids_bed, 1 lazy_sofa, 1 single_bed. Place the single_bed as the main anchor, then arrange desk, kids_bed, lazy_sofa, then add ceiling_lamp; keep ceiling_lamp paired_with single_bed; keep kids_bed paired_with single_bed; keep lazy_sofa paired_with single_bed. Respect these layout relations: ceiling_lamp paired_with single_bed; kids_bed paired_with single_bed; lazy_sofa paired_with single_bed; desk paired_with single_bed. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

## 14. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01 (goal_aligned_functional)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 2, 'kids_bed': 1, 'lounge_chair': 1}`
- image: `target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_target_semantic.png`
- context_image: `cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_goal_lostate_rich.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 2 desk, 1 kids_bed, 1 lounge_chair. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_functional:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 2 desk, 1 kids_bed, 1 lounge_chair. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_relation_rich:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 2 desk, 1 kids_bed, 1 lounge_chair. Place the kids_bed as the main anchor, then arrange desk, lounge_chair, then add ceiling_lamp; keep ceiling_lamp paired_with kids_bed; keep lounge_chair paired_with kids_bed; keep desk paired_with kids_bed. Respect these layout relations: ceiling_lamp paired_with kids_bed; lounge_chair paired_with kids_bed; desk paired_with kids_bed; ceiling_lamp closely_near lounge_chair. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

## 15. 36c96aa6-a318-4212-aecc-22a206d7b217_room_01 (goal_aligned_relation_rich)

- room_type: `elderlyroom`
- furniture_counts: `{'desk': 2}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_01_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Place two desks in the elderlyroom such that they are inside the room, do not overlap, use the exact palette, and follow architectural conditions.
```

prompt_llm_functional:

```text
Context_Control. Place two desks in the elderlyroom ensuring they are inside the room, avoid overlapping, use the exact palette, and adhere to architectural conditions.
```

prompt_llm_relation_rich:

```text
Context_Control. Place two desks in the elderlyroom such that they are inside the room, do not overlap, use the exact palette, and follow architectural conditions.
```

## 16. 36c96aa6-a318-4212-aecc-22a206d7b217_room_05 (goal_aligned_relation_rich)

- room_type: `bedroom`
- furniture_counts: `{'desk': 2, 'pendant_lamp': 1}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_goal_lostate_rich.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_05_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 2 desk, 1 pendant_lamp. Place the desk as the main anchor, then arrange pendant_lamp; keep pendant_lamp paired_with desk. Respect these layout relations: pendant_lamp paired_with desk. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

prompt_llm_functional:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 2 desk, 1 pendant_lamp. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_relation_rich:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 2 desk, 1 pendant_lamp. Place the desk as the main anchor, then arrange pendant_lamp; keep pendant_lamp paired_with desk. Respect these layout relations: pendant_lamp paired_with desk. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

## 17. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00 (goal_aligned_relation_rich)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 1, 'kids_bed': 1, 'lazy_sofa': 1, 'single_bed': 1}`
- image: `target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_target_semantic.png`
- context_image: `cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_goal_lostate_rich.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 1 desk, 1 kids_bed, 1 lazy_sofa, 1 single_bed. Place the single_bed as the main anchor, then arrange desk, kids_bed, lazy_sofa, then add ceiling_lamp; keep ceiling_lamp paired_with single_bed; keep kids_bed paired_with single_bed; keep lazy_sofa paired_with single_bed. Respect these layout relations: ceiling_lamp paired_with single_bed; kids_bed paired_with single_bed; lazy_sofa paired_with single_bed; desk paired_with single_bed. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

prompt_llm_functional:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 1 desk, 1 kids_bed, 1 lazy_sofa, 1 single_bed. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_relation_rich:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 1 desk, 1 kids_bed, 1 lazy_sofa, 1 single_bed. Place the single_bed as the main anchor, then arrange desk, kids_bed, lazy_sofa, then add ceiling_lamp; keep ceiling_lamp paired_with single_bed; keep kids_bed paired_with single_bed; keep lazy_sofa paired_with single_bed. Respect these layout relations: ceiling_lamp paired_with single_bed; kids_bed paired_with single_bed; lazy_sofa paired_with single_bed; desk paired_with single_bed. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

## 18. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01 (goal_aligned_relation_rich)

- room_type: `bedroom`
- furniture_counts: `{'ceiling_lamp': 1, 'desk': 2, 'kids_bed': 1, 'lounge_chair': 1}`
- image: `target/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_target_semantic.png`
- context_image: `cond/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_arch_condition.png`
- goal_lostate: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_goal_lostate_rich.json`
- prompt_package: `meta/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01_goal_aligned_llm_prompt_package.json`
- llm_actual_generation_used: `True`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 2 desk, 1 kids_bed, 1 lounge_chair. Place the kids_bed as the main anchor, then arrange desk, lounge_chair, then add ceiling_lamp; keep ceiling_lamp paired_with kids_bed; keep lounge_chair paired_with kids_bed; keep desk paired_with kids_bed. Respect these layout relations: ceiling_lamp paired_with kids_bed; lounge_chair paired_with kids_bed; desk paired_with kids_bed; ceiling_lamp closely_near lounge_chair. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

prompt_llm_functional:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 2 desk, 1 kids_bed, 1 lounge_chair. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation. Use only the required furniture categories.
```

prompt_llm_relation_rich:

```text
Context_Control. Create a top-down fixed-palette semantic bedroom layout with 1 ceiling_lamp, 2 desk, 1 kids_bed, 1 lounge_chair. Place the kids_bed as the main anchor, then arrange desk, lounge_chair, then add ceiling_lamp; keep ceiling_lamp paired_with kids_bed; keep lounge_chair paired_with kids_bed; keep desk paired_with kids_bed. Respect these layout relations: ceiling_lamp paired_with kids_bed; lounge_chair paired_with kids_bed; desk paired_with kids_bed; ceiling_lamp closely_near lounge_chair. Follow the architecture condition image and keep furniture inside the room with clear door and window circulation.
```

## 19. 36c96aa6-a318-4212-aecc-22a206d7b217_room_00 (basic_metric_v2)

- room_type: `livingroom`
- furniture_counts: `{}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_00_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_00_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_00_goal_lostate.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_00_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic livingroom layout. Use the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions. Required furniture: 1 required coffee_table for required_furniture, 4 required dining_chair for required_furniture, 1 required dining_table for required_furniture. Layout guidance: Include the required coffee_table. Include the required dining_chair. Include the required dining_table. Keep all furniture inside the room. Avoid furniture overlap. Use only the frozen semantic palette. Keep the door clearance area free. Keep all architectural clearance and non-placeable regions free. Use only frozen semantic categories and the frozen palette.
```

## 20. 36c96aa6-a318-4212-aecc-22a206d7b217_room_02 (basic_metric_v2)

- room_type: `study`
- furniture_counts: `{}`
- image: `target/36c96aa6-a318-4212-aecc-22a206d7b217_room_02_target_semantic.png`
- context_image: `cond/36c96aa6-a318-4212-aecc-22a206d7b217_room_02_arch_condition.png`
- goal_lostate: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_02_goal_lostate.json`
- prompt_package: `meta/36c96aa6-a318-4212-aecc-22a206d7b217_room_02_prompt_package.json`
- llm_actual_generation_used: `None`

Final metadata prompt:

```text
Context_Control. Create a top-down fixed-palette semantic study layout. Use the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions. Required furniture: 1 required armchair for required_furniture, 1 required desk for required_furniture. Layout guidance: Include the required armchair. Include the required desk. Keep all furniture inside the room. Avoid furniture overlap. Use only the frozen semantic palette. Keep all architectural clearance and non-placeable regions free. Use only frozen semantic categories and the frozen palette.
```

