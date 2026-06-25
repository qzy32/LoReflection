# Start Here

This is the short onboarding map for LoReflection. Use it before opening the
full project structure guide.

## Current Protocol

LoReflection is currently organized around:

- Planner-facing actions: ADD / REMOVE / TRANSLATE / ROTATE / SCALE / REPLACE
- semantic_repair4: ADD / REMOVE / TRANSLATE / REPLACE
- parametric_update: ROTATE / SCALE

ROTATE and SCALE are valid Planner actions, but they do not enter Qwen/DiffSynth
semantic repair metadata. They do not use `mask_spec` or `correction_prompt`.

## Read These First

1. `docs/CURRENT_PROJECT_STATE.md` - source of truth for the current pipeline and action routing.
2. `README.md` - short project overview and current C12/C13 status.
3. `README_SERVER.md` - how server-side training and data paths are handled.
4. `PROGRESS.md` - current milestone status and next step.
5. `docs/PROJECT_STRUCTURE_GUIDE.md` - full repository map.

## Current Interface

6. `artifacts/current_interface/repairplan.schema.json` - current Planner output schema.
7. `artifacts/current_interface/mask_spec.schema.json` - mask schema for semantic_repair4 only.
8. `tools/validate_current_repairplan.py` - validator for Planner outputs and examples.
9. `outputs/current_vlm_planner_handoff/` - handoff package for VLM Planner teammates.

## C12/C13 Data And Training

10. `reports/current_c12_input_manifest.json` - current semantic_repair4 sample manifest.
11. `docs/C12_REPAIR_OUTPUT_SANITIZER.md` - C12 data/sanitizer gate.
12. `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md` - C13 small overfit result.
13. `docs/EXPERIMENT_LOG_SEMANTIC_REPAIR4.md` - server runs, checkpoints, metrics, and decisions.
14. `configs/c13_semantic_repair4_overfit/` - C13 training config summaries.
15. `diffusion/train_diffsynth_qwen_inpaint_lora.sh` - local template for DiffSynth/Qwen inpaint LoRA training.
16. `docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md` - C14 medium data gate, loader dry-run, and GPU-memory training blocker.
17. `reports/c14_autonomous_pipeline_result.json` - machine-readable C14 status and next action.
18. `configs/c14_semantic_repair4_medium/` - local mirror of C14 medium training parameters.
19. `scripts/c14_train_*_20.sh` and `scripts/c14_train_mixed_80.sh` - server-side C14 command mirrors.
20. `docs/C14_3_PALETTE_CONTRACT_REPAIR_AND_RERUN.md` - explains the C14 palette-contract repair and why old C14.1 checkpoints are audit-only.
21. `configs/c14_3_semantic_repair4_palette_fixed/` - palette-fixed C14.3 clean rerun configs.
22. `scripts/c14_3_wait_and_run_palette_fixed.sh` - waits for a free A800 and launches the clean palette-fixed rerun.
23. `scripts/c14_4_wait_and_run_palette_fixed_clean_training.sh` - completed GPU-wait and clean-training executor used for C14.4.
24. `docs/C14_4_PALETTE_FIXED_CLEAN_TRAINING_RESULT.md` - first valid palette-fixed C14 training and evaluation result.
25. `reports/c14_4_palette_fixed_clean_training_result.json` - machine-readable C14.4 decision and metrics.

## If You Are A VLM Planner Teammate

Start with:

1. `outputs/current_vlm_planner_handoff/README_VLM_PLANNER_HANDOFF.md`
2. `outputs/current_vlm_planner_handoff/ACTION_PROTOCOL.md`
3. `outputs/current_vlm_planner_handoff/REPAIRPLAN_OUTPUT_SPEC.md`
4. `outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl`
5. `tools/validate_current_repairplan.py`

## If You Are A DiffSynth Training Teammate

Start with:

1. `README_SERVER.md`
2. `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`
3. `reports/c13_semantic_repair4_pipeline_result.json`
4. `outputs/semantic_repair4_overfit_dataset_v1/` - server-side dataset; not expected in the local checkout.
5. `outputs/manual_review/c13_overfit_*/step100_eval/`

## If You Are Debugging Data

Start with:

1. `reports/current_c12_input_manifest.json`
2. `reports/c12_sanitizer_eval.json`
3. `reports/c12_1_noop_replacement_report.json`
4. `outputs/manual_review/c12_sanitizer/`
5. `tools/validate_current_repairplan.py`

## If You Are Debugging Training Failure

Start with:

1. `reports/c13_semantic_repair4_pipeline_result.json`
2. `reports/c13_overfit_ADD.json`
3. `reports/c13_overfit_REMOVE.json`
4. `reports/c13_overfit_TRANSLATE.json`
5. `reports/c13_overfit_REPLACE.json`
6. `reports/c13_overfit_MIXED.json`
7. `tools/evaluate_c13_semantic_repair4_outputs.py`
8. `reports/c14_autonomous_pipeline_result.json`
9. `reports/c14_3_palette_contract_repair_result.json`
10. `reports/c14_3_evaluator_selftest_palette_fixed.json`

## Do Not Do This Without A New Protocol Decision

- Do not add ROTATE or SCALE to Qwen/DiffSynth semantic repair.
- Do not change taxonomy, palette, or semantic registry.
- Do not start larger semantic_repair4 training until the palette-fixed C14.3 20/action clean rerun has valid evaluator signals.
- Do not print server credentials or local environment files.
