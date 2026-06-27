# Opening Anchor Recovery Audit

## Scope
This audit does not regenerate the dataset, overwrite metadata, start training, or fabricate doors/windows. It scans existing full_semantic_compiled_main metadata and tests whether explicit scene-level 3D-FRONT Door/Window candidates can be assigned back to per-room Architecture JSON by boundary proximity.

## Findings
- 3D-FRONT JSON granularity: scene-level house/apartment JSON with multiple `scene.room[]` entries, not one JSON per room.
- Current adapter before this fix primarily used `room.children`; scene-level Door/Window not attached to a room could be missed.
- Rooms scanned: `16403`
- Rooms with door before recovery: `8855`
- Rooms with door after recovery: `15457`
- Rooms with window before recovery: `11263`
- Rooms with window after recovery: `12788`
- Major rooms scanned: `14305`
- Major rooms with door before recovery: `7912`
- Major rooms with door after recovery: `13581`
- Major rooms with window before recovery: `10003`
- Major rooms with window after recovery: `11426`
- Major rooms still without recoverable door: `724`
- Boundary source distribution: `{'room_floor_mesh': 16386, 'furniture_extent_fallback': 17}`
- Recovery source distribution: `{'scene_global_furniture_recovered': 24991, 'scene_global_mesh_recovered': 33430}`

## room_05 Explanation
For `36c96aa6-a318-4212-aecc-22a206d7b217_room_05`, the raw scene contains a global Door mesh/furniture, but `room_05` children do not include that Door. The recovery pass only assigns that global Door if it is near the room boundary; it does not fabricate a door.

`room_05` recovery result: `{'boundary_is_bbox_fallback': 'False', 'boundary_source': 'room_floor_mesh', 'door_anchor_count_after_recovery': '0', 'door_anchor_count_before': '0', 'door_recovered': 'False', 'door_recovery_source': '', 'is_major_room': 'True', 'room_type': 'bedroom', 'sample_id': '36c96aa6-a318-4212-aecc-22a206d7b217_room_05', 'source_scene_json': '/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front/3D-FRONT/36c96aa6-a318-4212-aecc-22a206d7b217.json', 'training_gate_status': 'drop_no_recoverable_door_anchor', 'window_anchor_count_after_recovery': '0', 'window_anchor_count_before': '0', 'window_recovered': 'False'}`

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
