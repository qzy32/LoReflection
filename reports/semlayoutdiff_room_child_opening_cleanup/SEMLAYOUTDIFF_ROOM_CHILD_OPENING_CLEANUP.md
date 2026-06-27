# SemLayoutDiff Room-child Opening Cleanup

## Policy
Current LoReflection opening policy is `semlayoutdiff_room_children_only`:

- 3D-FRONT JSON is scene-level.
- The adapter may read complete `data["mesh"]`.
- A room only has a door/window if that room's `scene.room[].children` references a `Door` / `Window` mesh.
- Scene-global Door/Window meshes not referenced by the current room are ignored.
- No scene-level geometry assignment is used.
- No fabricated door is allowed.

## Counts
- total_rooms_scanned: `16403`
- rooms_with_room_child_door: `5085`
- rooms_with_room_child_window: `6504`
- major_rooms_scanned: `14305`
- major_rooms_with_room_child_door: `4587`
- major_rooms_without_room_child_door: `9718`
- drop_no_room_child_door_count: `11318`

## Room 05 Result
`36c96aa6-a318-4212-aecc-22a206d7b217_room_05` has a scene-global Door in the source JSON, but this room's `children` list does not reference that Door mesh. Under the current policy it has `door_anchor_count = 0`, `qwen_input door_pixels = 0`, and is marked `drop_no_room_child_door_anchor`.

## Three Example Review
See `reports/semlayoutdiff_room_child_opening_cleanup/review_samples_3`.

## Recommendation
The existing full_semantic_compiled_main metadata was not regenerated. Next regeneration should filter with `has_room_child_door == true`; do not train on rooms that lack a room-child Door anchor if the training contract requires a visible door.
