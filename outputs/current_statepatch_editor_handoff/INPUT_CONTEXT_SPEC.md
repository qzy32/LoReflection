# StatePatch Editor Input Context Spec

The StatePatch editor input validates against
`schemas/statepatch_editor_input_context.schema.json`.

Required fields:

- `schema_version`: `statepatch-editor-input-context-v1`
- `task_tag`: `[STATEPATCH_EDITING]`
- `goal_lostate`
- `observed_lostate`
- `loreview`
- `architecture_ref` or `architecture_summary`
- `allowed_actions`
- `statepatch_output_spec`
- `verification_profile`

The input context is a diagnostic view. The VLM chooses a local repair in the
Observed LoState view; it does not write executable scene files directly.

Forbidden fields in this current context:

- `mask_spec`
- `repairplan_output_spec`
- `semantic_repair4` routing
- `control_mask`
- `blockwise_controlnet_inpaint_mask`

