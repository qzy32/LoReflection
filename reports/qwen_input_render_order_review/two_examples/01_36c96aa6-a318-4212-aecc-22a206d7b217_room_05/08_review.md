# Render Order Review

sample_id: `36c96aa6-a318-4212-aecc-22a206d7b217_room_05`

![side by side](06_side_by_side.png)

![human render order viz](07_human_render_order_viz_NOT_FOR_QWEN.png)

## Checks
- sample_id: `36c96aa6-a318-4212-aecc-22a206d7b217_room_05`
- has_lamp: `True`
- render_order_indices_monotonic: `True`
- lamp_last_if_present: `True`
- air_conditioner_priority_policy: `air_conditioner priority -20 if category appears in future registry/layout`
- protected_pixels_unchanged: `True`
- palette_exact: `True`
- overwritten_previous_furniture_px_total: `22`
- zero_written_object_count: `0`
- prompt_order_terms: `[]`
- looks_ok: `True`

## Files
- `03_target_render_debug.json`
- `04_render_order_table.csv`

