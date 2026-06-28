# Qwen Input Render Logic Review

- Training started: false
- Full dataset regenerated: false
- Existing metadata overwritten: false

## Answers

1. Current old renderer was simple boundary polygon plus anchors: true.
2. Old renderer lacked explicit room-local crop/padding/scale debug metadata: true.
3. Door/window min visible strip added: true.
4. New target is qwen_input byte copy plus furniture overlay: true.
5. Protected pixels byte-exact unchanged in sampled outputs: True.
6. wall_in_registry: False.
7. wall policies seen: ['no_wall_class_floor_void_boundary_only'].
8. Prompt updated to avoid promising visible wall/clearance/non-placeable classes: true.

## Samples
- `36c96aa6-a318-4212-aecc-22a206d7b217_room_00`: `reports/qwen_input_render_logic_review/two_examples/01_36c96aa6-a318-4212-aecc-22a206d7b217_room_00/44_review.md`, looks_ok=True, door_px=333, window_px=0, protected_unchanged=True
- `36c96aa6-a318-4212-aecc-22a206d7b217_room_01`: `reports/qwen_input_render_logic_review/two_examples/02_36c96aa6-a318-4212-aecc-22a206d7b217_room_01/44_review.md`, looks_ok=True, door_px=0, window_px=0, protected_unchanged=True

## Recommendation

Regenerate the full mainline package next if these two samples are accepted. Do not start training from the stale package.

## Verification

- git diff --check: pass
- residual grep: empty
- pytest: 59 passed, 1 warning
- tar: `reports/qwen_input_render_logic_review/qwen_input_render_logic_review.tar.gz`
