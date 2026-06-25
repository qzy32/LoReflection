# LoReflection

LoReflection is a closed-loop indoor semantic layout generation and repair system built around Goal/Observed LoState, LoReview, VLM Correction Planner outputs, and Qwen/DiffSynth semantic repair.

The current repository state is frozen around the repair protocol described in `docs/CURRENT_PROJECT_STATE.md`.

## Current Pipeline

User instruction + Architecture JSON
-> Target LoState Constructor
-> Goal LoState
-> Qwen-Image initial semantic layout generation
-> Programmatic State Observer
-> Observed LoState
-> Dual-Track Reviewer + LoRAM
-> LoReview
-> VLM Correction Planner
-> RepairPlan
-> semantic repair or parametric repair routing

## Current Action Protocol

Planner-facing canonical actions:

- ADD
- REMOVE
- TRANSLATE
- ROTATE
- SCALE
- REPLACE

Execution routing:

- semantic_repair4: ADD, REMOVE, TRANSLATE, REPLACE
- parametric_update: ROTATE, SCALE

ROTATE and SCALE are valid Planner actions, but they do not enter Qwen/DiffSynth semantic repair metadata. They update structured layout fields through parametric_update.

## Current Handoff

The current VLM Planner handoff package is:

- `outputs/current_vlm_planner_handoff/`
- `outputs/current_vlm_planner_handoff.zip`

The current interface schemas are:

- `artifacts/current_interface/repairplan.schema.json`
- `artifacts/current_interface/mask_spec.schema.json`
- `artifacts/current_interface/planner_input_context.schema.json`

Validate Planner outputs with:

```bash
python tools/validate_current_repairplan.py outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl --sft-jsonl
```

## C12 Input

C12 uses real converted EditRoom semantic samples from C11.10.

Only semantic_repair4 actions enter the Qwen/DiffSynth sanitizer path:

- ADD
- REMOVE
- TRANSLATE
- REPLACE

ROTATE and SCALE remain parametric_update and are excluded from current DiffSynth metadata.

See:

- `docs/C12_SANITIZER_CURRENT_PLAN.md`
- `reports/current_c12_input_manifest.json`
- `reports/c12_sanitizer_eval.json`
- `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`

Current C12 result: `C12_PASS` after replacing the no-op semantic samples.

Current C13 result: semantic_repair4 small Qwen/DiffSynth overfit completed for ADD, REMOVE, TRANSLATE, REPLACE, and a 12-row mixed run. All strict model gates are currently PARTIAL, so larger semantic_repair4 training is not yet allowed.

Current C14.1 result: the medium diagnostic dataset was built from real EditRoom conversion candidates with 20 rows/action, and the real DiffSynth `UnifiedDataset` dry-run passed for ADD, REMOVE, TRANSLATE, REPLACE, and MIXED_80 metadata. Auto-GPU resume selected GPU2, completed REMOVE / REPLACE / TRANSLATE / ADD to 300 steps each, and completed MIXED_80 to 320 steps.

Current C14.2 result: sampled image evaluation is blocked by a palette/evaluator contract issue, not yet a clean model-quality conclusion. `I_target` and oracle-copyback self-tests also fail because the C14 medium semantic PNGs are not encoded with `artifacts/semantic_registry_v2/palette_frozen.json` exactly. Do not expand to 50/action or larger training until `I_bad` and `I_target` are regenerated or adapted to the current frozen palette and the evaluator self-test passes.

Current C14.3 result: the palette-fixed medium dataset v2 has been regenerated
with exact frozen-palette RGBs using label-level old-palette to frozen-palette
mapping. The data gate, evaluator self-test, and DiffSynth loader dry-run all
pass. The previous C14.1 checkpoints are retained for audit but invalidated as
model-quality evidence because they were trained/evaluated under a palette
contract mismatch.

Final C14.4 status: the corrected `c14_4_fixedsteps` run completed on GPU0.
REMOVE, REPLACE, TRANSLATE, and ADD each completed 300 steps and produced
nonzero action-specific metrics. MIXED_80 also completed and was evaluated at
step 300. REMOVE reached 0.60 sampled edit success; the other actions remain
partial. Proceed to C15 prompt/mask/action-specific diagnosis, not 50/action.

See:

- `docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md`
- `reports/c14_autonomous_pipeline_result.json`
- `reports/c14_1_autogpu_resume_result.json`
- `reports/c14_2_training_inference_contract_result.json`
- `reports/c14_2_palette_contract_check.json`
- `reports/c14_3_palette_contract_repair_result.json`
- `reports/c14_3_evaluator_selftest_palette_fixed.json`
- `reports/c14_medium_data_gate.json`
- `reports/c14_diffsynth_loader_dryrun.json`

## Boundaries

- No model weights are stored in this repository.
- No external datasets are stored in this repository.
- Third-party official source checkouts and external data roots must not be deleted by repository cleanup steps.
- Current repair-protocol documentation should use only the current action and execution-mode names above.
