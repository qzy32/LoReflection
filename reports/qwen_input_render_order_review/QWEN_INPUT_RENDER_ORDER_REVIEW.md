# Qwen Input Render Order Review

- Training started: false
- Full dataset regenerated: false
- Existing metadata overwritten: false

## Answers

1. Previous overlay loop depended on layout JSON object order.
2. New policy sorts by priority ascending, area_px descending, category name, stable object id.
3. Low priority categories: air_conditioner, wall_air_conditioner, ceiling_air_conditioner, ceiling_fan.
4. High priority categories: pendant_lamp, ceiling_lamp, display_screen.
5. Prompt is unchanged semantically and does not mention render order.
6. Target remains qwen_input copy plus furniture overlay.

## Samples
- `36c96aa6-a318-4212-aecc-22a206d7b217_room_05`: `reports/qwen_input_render_order_review/two_examples/01_36c96aa6-a318-4212-aecc-22a206d7b217_room_05/08_review.md`, looks_ok=True, lamp_last=True, protected_unchanged=True
- `36c96aa6-a318-4212-aecc-22a206d7b217_room_00`: `reports/qwen_input_render_order_review/two_examples/02_36c96aa6-a318-4212-aecc-22a206d7b217_room_00/08_review.md`, looks_ok=True, lamp_last=True, protected_unchanged=True

## Recommendation

Regenerate the full package next if these reviews are accepted. Do not start training from stale rendered targets.

## Verification

- git diff --check: pass
- residual grep: empty
- pytest: 64 passed, 1 warning
- tar: `reports/qwen_input_render_order_review/qwen_input_render_order_review.tar.gz`
