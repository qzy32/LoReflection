# StatePatch Output Spec

The StatePatch editor returns exactly one JSON object that validates against
`schemas/statepatch.schema.json`.

Required top-level fields:

- `schema_version`: must be `statepatch-v1.2`
- `patch_id`
- `patch_target_space`: must be `observed_lostate_view`
- `execution_target_space`: `layout_json` or `scene_json`
- `source_observed_state_id`
- `action_type`: `ADD`, `REMOVE`, `TRANSLATE`, `ROTATE`, `SCALE`, or `REPLACE`
- `target.target_ref`: an `obs:` reference from Observed LoState
- `target.expected_category`
- `state_field_updates`: required for all actions except `REMOVE`
- `reason`
- `constraints_to_satisfy`
- `protected_refs`

Allowed update fields:

- `center_m`
- `orientation_deg`
- `size_m`
- `category`
- `asset_id`
- `new_instance`

The VLM must not output:

- a complete Edited LoState
- a complete layout JSON or scene JSON
- `source_json_path`
- low-level engine uid values
- `RepairPlan`
- `mask_spec`
- `control_mask`
- `I_bad` or `I_target`
- `blockwise_controlnet_image`
- `blockwise_controlnet_inpaint_mask`

The executor resolves `target.target_ref` against Observed LoState and maps the
allowed state field updates to candidate layout JSON / scene JSON.

TODO: `ADD` currently still requires `target.target_ref` in the
`observed_lostate_view`. For future StatePatch SFT, `ADD` should use an observed
room, region, or anchor reference such as `obs:room_001`,
`obs:free_region_001`, or `obs:anchor_001`. This does not block Qwen
Architecture In-Context P0 dataset construction.
