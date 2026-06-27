# Current StatePatch Editor Handoff

This is the current VLM handoff for LoReflection local repair.

The current mainline is:

```text
Goal LoState + Observed LoState + LoReview
-> Qwen3.5-VL StatePatch Editor
-> StatePatch
-> StatePatch Executor + Write-back Serializer
-> candidate layout JSON / scene JSON
-> rebuilt Observed LoState
-> Verifier / Reviewer / AcceptanceController
```

The VLM does not output a full Edited LoState. It does not output layout JSON,
scene JSON, `source_json_path`, engineering uid values, `RepairPlan`,
`mask_spec`, `control_mask`, `I_bad`, `I_target`, or blockwise ControlNet
fields.

The old `outputs/current_vlm_planner_handoff/` package is retained only as a
legacy RepairPlan planner handoff for the C12-C14 historical
semantic_repair4/inpaint baseline.

## Files

- `STATEPATCH_OUTPUT_SPEC.md`: output contract for StatePatch v1.2.
- `INPUT_CONTEXT_SPEC.md`: input context contract for the StatePatch editor.
- `statepatch_sft_minimal_examples.jsonl`: minimal SFT-style examples.
- `schemas/statepatch.schema.json`: local copy of the current StatePatch schema.
- `schemas/statepatch_editor_input_context.schema.json`: local copy of the input
  context schema.

## Validation

From the repository root:

```bash
python tools/validate_current_statepatch.py outputs/current_statepatch_editor_handoff/statepatch_sft_minimal_examples.jsonl --sft-jsonl
```


- `STATEPATCH_SFT_STRICT_PROTOCOL.md`: strict training/inference subset for StatePatch SFT.

## Strict SFT Protocol

For VLM SFT and inference, use `STATEPATCH_SFT_STRICT_PROTOCOL.md`.

The JSON schema is intentionally wider than the training subset. The strict subset is the current training/inference contract:

- ADD uses `new_instance.category/asset_id/size_hint/placement_hint`; the executor decides concrete placement.
- REMOVE uses `target.target_ref`.
- TRANSLATE uses only `center_m.relative_delta.delta_m`.
- ROTATE uses only `orientation_deg.relative_delta.delta_deg`.
- SCALE uses only `size_m.relative_scale.scale_xy`.
- REPLACE uses `category` / `asset_id` and optional relative scale.
- The VLM must not output bbox, footprint, complete layout JSON, or complete scene JSON.
