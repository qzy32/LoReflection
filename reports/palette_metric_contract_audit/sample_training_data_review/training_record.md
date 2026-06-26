# One Qwen Training Record Review

Status: **NOT VERIFIED locally**.

Preferred sample id: `36c96aa6-a318-4212-aecc-22a206d7b217_room_00`

The local snapshot does not contain the server P1 metric_v2 data package, so the actual `context_image`, `target_semantic`, `Goal LoState`, `prompt_package`, `active_palette_entries`, and `metric_transform` could not be copied without fabricating data.

Run the audit package on A800 after SSH is available to populate this folder with:

- `context_image.png`
- `target_semantic.png`
- `side_by_side_context_target.png`
- `target_with_palette_legend.png`
- `goal_lostate.json`
- `prompt_package.json`
- `palette_entries.json`
- `metric_transform.json`

Prediction image not included because eval output images were not available locally.
