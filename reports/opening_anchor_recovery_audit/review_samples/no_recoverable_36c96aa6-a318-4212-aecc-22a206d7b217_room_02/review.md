# Opening Anchor Recovery Review

sample_id: `36c96aa6-a318-4212-aecc-22a206d7b217_room_02`

## Status
- room_type: `study`
- door before: `0`
- window before: `0`
- door after: `0`
- window after: `0`
- new_qwen_input door pixels: `0`
- new_qwen_input window pixels: `0`
- training_gate_status: `drop_no_recoverable_door_anchor`

## Images
![old qwen input](old_qwen_input.png)
![new qwen input](new_qwen_input_with_recovered_door.png)
![new target](new_target_full_semantic.png)
![human debug](human_debug_opening_assignment_NOT_FOR_QWEN.png)

Recovered anchors are assigned from explicit scene-level Door/Window candidates only when they are near the room floor boundary. No random or fabricated door is inserted.
