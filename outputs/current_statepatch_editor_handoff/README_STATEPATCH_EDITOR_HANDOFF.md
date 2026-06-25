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

