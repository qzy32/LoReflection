# LoReflection Progress

## Current State

The repository is currently frozen at the repair-protocol handoff state.

Current Planner-facing actions:

- ADD
- REMOVE
- TRANSLATE
- ROTATE
- SCALE
- REPLACE

Current execution routing:

- semantic_repair4: ADD, REMOVE, TRANSLATE, REPLACE
- parametric_update: ROTATE, SCALE

ROTATE and SCALE are valid Planner actions, but they do not enter Qwen/DiffSynth semantic repair.

## Current Deliverables

- `docs/CURRENT_PROJECT_STATE.md`
- `outputs/current_vlm_planner_handoff/`
- `artifacts/current_interface/`
- `reports/current_c12_input_manifest.json`
- `reports/c11_11_repository_cleanup_report.json`

## Validation

Current tests:

```bash
python -m pytest tests/test_current_action_protocol.py tests/test_current_repairplan_schema.py tests/test_current_vlm_handoff.py tests/test_current_c12_manifest.py tests/test_no_deprecated_terms_in_current_docs.py -q
python tools/validate_current_repairplan.py outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl --sft-jsonl
```

Expected result:

- current protocol tests pass
- current Planner examples validate
- current C12 manifest excludes ROTATE and SCALE from DiffSynth metadata

## C12/C13 Status

C12 sanitizer was rerun after replacing no-op rows and now reports `C12_PASS`.

C13 Qwen/DiffSynth small overfit completed for ADD, REMOVE, TRANSLATE, REPLACE, and a 12-row mixed run. All strict model gates are currently PARTIAL. This means the data, loader, and training script are usable, but larger semantic_repair4 training should wait for targeted diagnosis of allowed-label violations, extra components, and palette adherence.

C12 and C13 status:

- `reports/c12_sanitizer_eval.json`
- `reports/c13_semantic_repair4_pipeline_result.json`
- `docs/C12_REPAIR_OUTPUT_SANITIZER.md`
- `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`
- `docs/EXPERIMENT_LOG_SEMANTIC_REPAIR4.md`

## Next Step

Diagnose C13 PARTIAL model outputs and decide whether to run a targeted 300-step continuation or adjust postprocess-aware evaluation. Do not start larger semantic_repair4 training yet.

## C14 Medium Diagnostic Status

C14 medium-scale diagnostic preparation completed on the server side:

- medium dataset: 20 rows/action, 80 rows total
- actions included: ADD, REMOVE, TRANSLATE, REPLACE
- actions excluded from Qwen/DiffSynth semantic repair: ROTATE, SCALE
- data gate: C14_DATA_PASS
- DiffSynth UnifiedDataset dry-run: PASS

Initial training was blocked by GPU memory, but C14.1 auto-GPU resume later selected a clear A800 GPU and completed the medium diagnostic training schedule:

- REMOVE: 300 steps
- REPLACE: 300 steps
- TRANSLATE: 300 steps
- ADD: 300 steps
- MIXED_80: 320 steps

Step-300 image evaluation on sampled rows is still not successful: edit_success remains 0, nonmask copyback is 1.0, snapped palette validity is 1.0, and allowed-label violations remain high. This means the environment and training loop are now usable, but semantic output quality is not ready for 50/action expansion.

Current C14 references:

- `docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md`
- `reports/c14_autonomous_pipeline_result.json`
- `reports/c14_1_autogpu_resume_result.json`
- `reports/c14_1_autogpu_image_eval_summary.json`
- `reports/c14_medium_dataset_manifest.json`
- `reports/c14_medium_data_gate.json`
- `reports/c14_diffsynth_loader_dryrun.json`

## C14.2 Training-Inference Contract Diagnosis

C14.2 diagnosed the C14.1 contradiction: low training loss but failed sampled image evaluation.

The blocking root cause is now `PALETTE_CONTRACT_FAIL causing EVAL_FAIL`.

Evidence:

- `I_target` and oracle-copyback evaluator self-tests also fail, so the sampled eval cannot yet be trusted as a pure model-quality signal.
- C14 medium metadata paths, binary masks, changed-region coverage, and outside-mask equality pass.
- A representative C14 medium sample has `I_target_exact_palette_ratio = 0.0` and `I_bad_exact_palette_ratio = 0.0` against `artifacts/semantic_registry_v2/palette_frozen.json`.
- The same sample has valid mask coverage (`changed_pixels_inside_mask = 1419`, `mask_area_px = 2891`) and outside-mask equality.

Current C14.2 references:

- `reports/c14_2_training_inference_contract_result.json`
- `reports/c14_2_palette_contract_check.json`
- `reports/c14_2_evaluator_selftest.json`
- `docs/C14_2_TRAINING_INFERENCE_CONTRACT_DIAGNOSIS.md`
- `docs/C14_2_FAILURE_DIAGNOSIS.md`

Next executable step: fix or regenerate C14 semantic_repair4 samples so `I_bad` and `I_target` use the current frozen palette exactly, then rerun C14 data gate and evaluator self-test. Do not continue 600/1000-step training, expand to 50/action, or start larger semantic_repair4 training until the palette/evaluator contract passes.

## C14.3 Palette Contract Repair

C14.3 regenerated the C14 medium dataset as:

```text
outputs/semantic_repair4_medium_dataset_v2_palette_fixed/
```

The repair used label-level mapping from the SemLayoutDiff native palette to
`artifacts/semantic_registry_v2/palette_frozen.json`. It did not change the
taxonomy, semantic registry, action protocol, or frozen palette.

Current C14.3 gates:

- palette audit: `PALETTE_MISMATCH_REPAIRABLE_BY_LABEL`
- data gate: `C14_3_DATA_PASS`
- evaluator self-test: `EVAL_OK`
- DiffSynth loader dry-run: `LOADER_PASS`
- old C14.1 checkpoints: retained for audit, invalidated as model-quality evidence

The v2 evaluator self-test now behaves correctly: `I_target` and oracle copyback
pass on all 80 rows, while `I_bad` and random fixed-palette predictions fail.

Clean palette-fixed training is deferred only because the A800 server currently
has no GPU with at least 60000 MiB free memory. The wait-and-run entry is:

```bash
bash scripts/c14_3_wait_and_run_palette_fixed.sh
```

Do not expand to 50/action until the palette-fixed 20/action clean rerun produces
valid evaluator signals.

## C14.4 Palette-Fixed Clean Training Complete

C14.4 selected GPU0 with 81219 MiB free and completed the corrected
`c14_4_fixedsteps` run:

- REMOVE: 300 steps, edit success 0.60, action IoU 0.914
- REPLACE: 300 steps, action IoU 0.611
- TRANSLATE: 300 steps, action IoU 0.683
- ADD: 300 steps, action IoU 0.806
- MIXED_80: step-300 action IoU 0.800

All runs retained snapped palette validity 1.0 and nonmask equality 1.0. This
is the first valid palette-fixed C14 model-quality result. The next step is C15
prompt/mask/action-specific diagnosis; 50/action expansion remains blocked.
