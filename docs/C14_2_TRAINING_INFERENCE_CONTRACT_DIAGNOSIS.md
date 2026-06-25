# C14.2 Training-Inference Contract Diagnosis

Source of truth: `docs/CURRENT_PROJECT_STATE.md`.

Current protocol is unchanged:

- semantic_repair4: ADD, REMOVE, TRANSLATE, REPLACE
- parametric_update: ROTATE, SCALE

ROTATE and SCALE remain Planner actions only for structured `parametric_update`; they do not enter Qwen/DiffSynth semantic repair, DiffSynth metadata, `mask_spec`, or `correction_prompt`.

## Diagnosis Result

Primary root cause:

```text
PALETTE_CONTRACT_FAIL causing EVAL_FAIL
```

C14.1 training itself completed, but C14.2 found that the sampled image evaluation cannot be trusted as a pure model-quality signal yet. The evaluator self-test failed even when `I_target` or oracle copyback was used as the prediction.

## Evidence

The current evaluator loads the frozen palette from:

```text
artifacts/semantic_registry_v2/palette_frozen.json
```

A representative C14 medium sample showed:

```text
sample:
  remove_001_015ed8e0-35dc-41ab-9a9e-b3dbba4ec64a_MasterBedroom-33296_remove-0_0

I_target_exact_palette_ratio: 0.0
I_bad_exact_palette_ratio: 0.0
target_equals_snapped_target_inside_mask_ratio: 0.0
bad_equals_target_outside_mask_ratio: 1.0
changed_pixels_inside_mask: 1419
mask_area_px: 2891
```

Interpretation:

- The mask and edit geometry are valid for the audited sample.
- Outside-mask equality is valid.
- The blocking issue is that `I_bad` and `I_target` are not encoded with the current frozen palette.
- Therefore the evaluator snaps predictions to one palette and compares against target RGB from another palette encoding.
- This explains why even `I_target` as prediction gets masked pixel accuracy 0.

## What This Rules Out For Now

The current evidence does not prove that the model failed to learn. It proves that sampled image metrics are invalid until the palette contract is fixed.

Do not make conclusions about:

- prompt conditioning
- mask polarity
- LoRA checkpoint effectiveness
- model undertraining
- sanitizer behavior

until `I_target` and oracle-copyback evaluator self-tests pass under the current frozen palette.

## Reports

- `reports/c14_2_training_inference_contract_result.json`
- `reports/c14_2_palette_contract_check.json`
- `reports/c14_2_evaluator_selftest.json`
- `reports/c14_2_metadata_contract_check.json`
- `reports/c14_2_palette_sanitizer_impact.json`
- `reports/c14_2_per_category_failure_diagnosis.json`

## Decision

Do not continue 600/1000-step training.

Do not expand to 50/action.

Do not start larger semantic_repair4 training.

Next executable step:

```text
Fix or regenerate C14 semantic_repair4 samples so I_bad and I_target use artifacts/semantic_registry_v2/palette_frozen.json exactly.
Then rerun:
  1. exact palette validation in the C14 data gate
  2. evaluator self-test with I_target / oracle / I_bad / random
  3. only then checkpoint, mask, and prompt ablations if needed
```

## C14.3 Follow-up

C14.3 completed that repair path. The C14 medium dataset was regenerated as
`outputs/semantic_repair4_medium_dataset_v2_palette_fixed/` using exact frozen
palette RGBs. The data gate, evaluator self-test, and DiffSynth loader dry-run
now pass.

The first C14.3 self-test also exposed a narrower allowed-label policy issue:
some white-mask target regions contain fixed semantic labels that must be valid
inside the repaint region. The v2 repair augmented `allowed_labels` with all
frozen semantic ids actually present in `I_target` inside the binary white mask.
After that repair:

- `I_target`: 80 / 80 edit_success
- oracle copyback: 80 / 80 edit_success
- `I_bad`: 0 / 80 edit_success
- random fixed-palette prediction: 0 / 80 edit_success

The next step is the clean palette-fixed 20/action rerun, currently deferred
until an A800 has at least 60000 MiB free memory.
