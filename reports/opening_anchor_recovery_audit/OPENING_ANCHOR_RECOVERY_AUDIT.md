# Opening Anchor Recovery Audit

## Scope
This audit does not regenerate the dataset, overwrite metadata, start training, or fabricate doors/windows. It scans existing full_semantic_compiled_main metadata and tests whether explicit scene-level 3D-FRONT Door/Window candidates can be assigned back to per-room Architecture JSON by boundary proximity.

## Findings
- 3D-FRONT JSON granularity: scene-level house/apartment JSON with multiple `scene.room[]` entries, not one JSON per room.
- Current adapter before this fix primarily used `room.children`; scene-level Door/Window not attached to a room could be missed.
- Rooms scanned: `200`
- Rooms with door before recovery: `113`
- Rooms with door after recovery: `187`
- Rooms with window before recovery: `130`
- Rooms with window after recovery: `157`
- Major rooms scanned: `175`
- Major rooms with door before recovery: `103`
- Major rooms with door after recovery: `167`
- Major rooms with window before recovery: `115`
- Major rooms with window after recovery: `141`
- Major rooms still without recoverable door: `8`
- Boundary source distribution: `{'room_floor_mesh': 200}`
- Recovery source distribution: `{'scene_global_furniture_recovered': 340, 'scene_global_mesh_recovered': 537}`

## room_05 Explanation
For `36c96aa6-a318-4212-aecc-22a206d7b217_room_05`, the raw scene contains a global Door mesh/furniture, but `room_05` children do not include that Door. The recovery pass only assigns that global Door if it is near the room boundary; it does not fabricate a door.

## Gate Policy
Major room types require at least one door/opening anchor. If no explicit candidate can be recovered, the room should be dropped from Qwen training rather than patched with a fake door.

## Outputs
- `room_opening_coverage.csv`
- `recovered_opening_candidates.csv`
- `no_recoverable_door_rooms.csv`
- `boundary_source_audit.csv`
- `review_samples/`

## Recommendation
Do not train on the old full_semantic_compiled_main package. Next step is to regenerate the full package with recovered opening anchors and drop major rooms that still have no recoverable door.
