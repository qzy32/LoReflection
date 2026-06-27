# Opening Anchor Recovery Review

sample_id: `faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00`

## Status
- room_type: `bedroom`
- door before: `0`
- window before: `2`
- door after: `4`
- window after: `3`
- new_qwen_input door pixels: `785`
- new_qwen_input window pixels: `672`
- training_gate_status: `pass`

## Images
![old qwen input](old_qwen_input.png)
![new qwen input](new_qwen_input_with_recovered_door.png)
![new target](new_target_full_semantic.png)
![human debug](human_debug_opening_assignment_NOT_FOR_QWEN.png)

Recovered anchors are assigned from explicit scene-level Door/Window candidates only when they are near the room floor boundary. No random or fabricated door is inserted.
