# Beginner Code Reading Manual

## 1. How Not To Read This Repository

Do not read the repository linearly. It contains current code, generated reports,
server mirrors, manual review images, and older exploratory material.

Do not start from:

- every file under `outputs/`
- `third_party/`
- every image in `manual_review`
- generated reports before reading the current protocol
- folders marked legacy or NEEDS_REVIEW in the project structure index

Start from current mainline files:

1. `docs/CURRENT_PROJECT_STATE.md`
2. `docs/START_HERE.md`
3. `README.md`
4. `artifacts/current_interface/repairplan.schema.json`
5. `tools/validate_current_repairplan.py`
6. `docs/C12_REPAIR_OUTPUT_SANITIZER.md`
7. `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`
8. `docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md`

## 2. One-Sentence Project Explanation

LoReflection is a closed-loop indoor semantic layout generation and repair
project: it generates a room semantic layout, reads that image back into state,
reviews mismatches, asks a VLM Planner for a `RepairPlan` plus `mask_spec`,
converts the mask plan into a binary `control_mask`, sends local repairs to
Qwen/DiffSynth, and then re-observes and evaluates the result.

## 3. Current Source Of Truth

The source of truth is `docs/CURRENT_PROJECT_STATE.md`.

Planner-facing actions:

- ADD
- REMOVE
- TRANSLATE
- ROTATE
- SCALE
- REPLACE

Current execution routes:

- semantic_repair4: ADD, REMOVE, TRANSLATE, REPLACE
- parametric_update: ROTATE, SCALE

ROTATE and SCALE are valid VLM Planner actions. They do not enter Qwen/DiffSynth
semantic repair, do not enter DiffSynth metadata, do not carry `mask_spec`, and
do not carry `correction_prompt`. They update structured state fields through
`parametric_update`.

## 4. End-To-End Flow

### User instruction + Architecture JSON

The user describes the room and constraints. Architecture JSON stores room type,
room shell, doors, windows, and other fixed context. Read
`docs/CURRENT_PROJECT_STATE.md`, `README.md`, and schemas under
`artifacts/current_interface/`.

### Target LoState Constructor -> Goal LoState

The target state is the desired structured layout. This repository documents the
current contract more clearly than any one beginner-facing constructor file. If
you need code, use `docs/PROJECT_STRUCTURE_FILE_INDEX.json` to locate
`data_pipeline/` and `loreflection/` entries.

### Qwen-Image initial semantic layout

Qwen produces a fixed-palette top-down semantic layout. Current repair training
focuses on local semantic repair after review, not on changing the initial
generation route.

### Programmatic State Observer -> Observed LoState

The observer parses the semantic layout back into structured state. Related
areas include `runtime/`, `loreflection/`, `tools/validate_observer_roundtrip.py`,
and observer reports such as `reports/observer_roundtrip_validation.json`.

### Dual-Track Reviewer + LoRAM -> LoReview

The reviewer compares Goal LoState and Observed LoState and emits issues. New
readers should understand the schema and reports before diving into reviewer
internals.

### VLM Correction Planner -> RepairPlan + mask_spec

The current VLM handoff lives in:

- `outputs/current_vlm_planner_handoff/README_VLM_PLANNER_HANDOFF.md`
- `outputs/current_vlm_planner_handoff/ACTION_PROTOCOL.md`
- `outputs/current_vlm_planner_handoff/REPAIRPLAN_OUTPUT_SPEC.md`
- `outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl`
- `artifacts/current_interface/repairplan.schema.json`
- `artifacts/current_interface/mask_spec.schema.json`
- `tools/validate_current_repairplan.py`

### Mask Tensor Adapter -> binary control_mask

`mask_spec` is symbolic. It describes components, roles, geometry, allowed
labels, and operation hints. Runtime code turns it into a binary `control_mask`:
white/high means repaint; black/low means preserve. Related files:
`runtime/mask_tensor_adapter.py` and `artifacts/current_interface/mask_spec.schema.json`.

### Qwen/DiffSynth semantic repair

Only semantic_repair4 actions enter this stage. DiffSynth metadata uses:

- `image` = I_target
- `blockwise_controlnet_image` = I_bad
- `blockwise_controlnet_inpaint_mask` = control_mask
- `prompt` = correction_prompt

Read `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`,
`docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md`,
`docs/EXPERIMENT_LOG_SEMANTIC_REPAIR4.md`,
`configs/c13_semantic_repair4_overfit/`,
`configs/c14_semantic_repair4_medium/`, and `scripts/c13_train_*.sh` /
`scripts/c14_train_*_20.sh`.

### raw output -> snapped output -> sanitized output -> evaluator

The evaluator loads model outputs, snaps them to the frozen palette, applies
copyback/sanitizer rules, and reports metrics. The key evaluator is
`tools/evaluate_c13_semantic_repair4_outputs.py`.

## 5. Ten-Chapter Reading Order

### Chapter 1: Project Current Mainline

- Goal: know the current pipeline and scope.
- Must read: `docs/CURRENT_PROJECT_STATE.md`, `docs/START_HERE.md`, `README.md`, `PROGRESS.md`.
- Optional: `docs/PROJECT_STRUCTURE_GUIDE.md`.
- Do not read first: generated image folders and old exploratory reports.
- Questions: What is semantic_repair4? What is parametric_update? What is the next safe step?
- Key concepts: source of truth, current protocol, generated artifact, server-side training.
- Exercise: write the six Planner actions and mark which four train Qwen/DiffSynth.
- Self-test: why should ROTATE and SCALE not appear in DiffSynth metadata?
- Common mistake: treating every old report as current.

### Chapter 2: Current Action Protocol

- Goal: understand actions and routing.
- Must read: `outputs/current_vlm_planner_handoff/ACTION_PROTOCOL.md`, `artifacts/current_interface/repairplan.schema.json`.
- Optional: `outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl`.
- Do not read first: previous candidate handoff packages.
- Questions: Which actions need `mask_spec`? Which actions need `parametric_delta`?
- Key concepts: Planner action, execution mode, semantic repair, structured update.
- Exercise: inspect ROTATE and SCALE examples and verify `mask_spec` is null.
- Self-test: what route does TRANSLATE use now?
- Common mistake: assuming TRANSLATE is structured-only.

### Chapter 3: RepairPlan / mask_spec / planner_input_context

- Goal: understand the VLM output contract.
- Must read: current schemas and `tools/validate_current_repairplan.py`.
- Optional: current schema tests.
- Do not read first: older schemas under `schemas/` unless a test points there.
- Questions: What does `target_count_delta` mean? What are `old_region` and `new_region`?
- Key concepts: schema validation, cross-field validation, allowed labels, operation hints.
- Exercise: run the validator on current minimal examples.
- Self-test: why does TRANSLATE require `allow_disconnected = true`?
- Common mistake: thinking JSON Schema alone catches all semantic errors.

### Chapter 4: VLM Handoff

- Goal: know what the VLM teammate receives and returns.
- Must read: all files in `outputs/current_vlm_planner_handoff/`.
- Optional: `artifacts/current_interface/manifest.json`.
- Do not read first: previous handoff packages.
- Questions: What must the VLM not output? What fields are required in every RepairPlan?
- Key concepts: SFT example, assistant JSON, Planner input context.
- Exercise: copy one assistant output into a JSON file and validate it.
- Self-test: why must the VLM not output a raw binary mask?
- Common mistake: confusing symbolic `mask_spec` with image `control_mask`.

### Chapter 5: C12 Data Gate And Sanitizer

- Goal: know how repair samples are checked before training.
- Must read: `docs/C12_REPAIR_OUTPUT_SANITIZER.md`, `reports/current_c12_input_manifest.json`, `reports/c12_sanitizer_eval.json`.
- Optional: `reports/c12_sanitizer_policy_sweep.json`, `outputs/manual_review/c12_sanitizer/`.
- Do not read first: individual PNGs unless a report points to a sample.
- Questions: What is oracle copyback? What is nonmask equality? What threshold was selected?
- Key concepts: sanitizer, copyback, allowed-label filtering, no-op filtering.
- Exercise: trace one manifest row from I_bad to I_target to control_mask.
- Self-test: what fails if a sample has zero changed pixels in the white mask?
- Common mistake: training on rows that pass schema but fail data semantics.

### Chapter 6: DiffSynth Metadata And Training Data

- Goal: understand the dataset contract.
- Must read: `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`, `reports/c13_semantic_repair4_pipeline_result.json`, `reports/c14_diffsynth_loader_dryrun.json`.
- Optional: server dataset folders listed in reports.
- Do not read first: local `outputs/` if the dataset is only on the server.
- Questions: What are I_bad, I_target, control_mask, prompt? Why is `image` the target?
- Key concepts: metadata row, condition image, binary mask, text condition.
- Exercise: open one metadata CSV row and identify all four file paths.
- Self-test: what breaks if `image` points to I_bad?
- Common mistake: reversing I_bad and I_target.

### Chapter 7: C13 Small Overfit

- Goal: understand the first Qwen/DiffSynth training proof.
- Must read: `docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`, `reports/c13_overfit_*.json`.
- Optional: `outputs/manual_review/c13_overfit_*/`.
- Do not read first: checkpoint binaries unless evaluating outputs.
- Questions: Which action learned best? Why are gates still PARTIAL?
- Key concepts: overfit, step-100 checkpoint, strict edit gate, manual review.
- Exercise: compare REMOVE and ADD metrics.
- Self-test: why can palette validity be 1.0 but edit_success still fail?
- Common mistake: calling PARTIAL a final success.

### Chapter 8: C14 Medium Diagnostic Training

- Goal: understand the 20/action diagnostic stage.
- Must read: C14 docs and `reports/c14_1_autogpu_resume_result.json`.
- Optional: C14 configs and scripts.
- Do not read first: 50/action expansion plans.
- Questions: Did data pass? Did training run? Did image eval pass?
- Key concepts: medium dataset, loader dry-run, GPU audit, training stability vs output quality.
- Exercise: read `reports/c14_1_autogpu_image_eval_summary.csv` and identify the blocker.
- Self-test: why is the next step not larger training?
- Common mistake: treating stable loss as semantic repair success.

### Chapter 9: Evaluator And Manual Review

- Goal: know how outputs are judged.
- Must read: `tools/evaluate_c13_semantic_repair4_outputs.py`, `reports/c14_1_autogpu_image_eval_summary.json`.
- Optional: visual folders referenced by reports.
- Do not read first: every generated image.
- Questions: What is raw output? What is snapped output? What is sanitized output?
- Key concepts: palette snapping, copyback, connected components, IoU, edit_success.
- Exercise: find one sample with high allowed-label violations and inspect its output folder.
- Self-test: why does nonmask equality matter?
- Common mistake: judging only the raw image without snapped/sanitized metrics.

### Chapter 10: Tests / Validator / Safe Changes

- Goal: learn how to change code safely.
- Must read: `tools/validate_current_repairplan.py` and current protocol tests.
- Optional: `reports/current_deprecated_term_audit.json`.
- Do not read first: broad refactors.
- Questions: Which tests protect action routing? Which tests protect C12 metadata?
- Key concepts: current tests, validator first, docs after code.
- Exercise: run validator and current pytest set.
- Self-test: what must you update after changing a schema?
- Common mistake: editing examples without running the validator.

## 6. What You Should Know After Reading

You should be able to explain the current protocol, validate a RepairPlan, trace
a semantic repair sample into DiffSynth metadata, identify training configs and
checkpoints, read C13/C14 reports, and know why the current next step is diagnosis
rather than scale-up.
