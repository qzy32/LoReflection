# Module And Folder Explanation

## `artifacts/`

Frozen interface and semantic registry artifacts. Current mainline lives in
`artifacts/current_interface/`: `repairplan.schema.json`, `mask_spec.schema.json`,
`planner_input_context.schema.json`, and `manifest.json`. Do not casually edit
current schemas or frozen palette/registry files.

## `configs/`

Configuration files for converters, sanitizer, category/palette mapping, and
training summaries. Current training config folders are
`configs/c13_semantic_repair4_overfit/` and `configs/c14_semantic_repair4_medium/`.

## `data_pipeline/`

Older/local data-building scripts for LoState, LoReview, planner SFT,
perturbations, and semantic layouts. Use `PROJECT_STRUCTURE_FILE_INDEX` before
editing anything here.

## `diffusion/`

Local DiffSynth/Qwen helper templates. `train_diffsynth_qwen_inpaint_lora.sh` is
a template, not the exact C14 run command.

## `docs/`

Human-readable documentation, current state docs, source audits, and experiment
notes. Start with `CURRENT_PROJECT_STATE.md`, `START_HERE.md`, and the C12/C13/C14
docs.

## `eval/`

Evaluation conversion and metric scripts. Current semantic repair eval is mainly
documented through `tools/evaluate_c13_semantic_repair4_outputs.py`.

## `examples/`

Toy and smoke examples. Useful for schema learning, but do not confuse them with
real EditRoom-converted semantic repair data.

## `experiments/`

Experiment organization if present. Treat as NEEDS_REVIEW unless a current
report points to a specific file.

## `loreflection/`

Project package code. Read this after you know which pipeline component you are
debugging.

## `outputs/`

Generated artifacts, handoff packages, dataset packages, manual review images,
and training outputs. Current important subset: `outputs/current_vlm_planner_handoff/`.
The full C13/C14 datasets and checkpoints are primarily server-side and recorded
in reports.

## `reports/`

Machine-readable evidence from audits, gates, training, and evaluation. Start
with `current_c12_input_manifest.json`, `c12_sanitizer_eval.json`,
`c13_semantic_repair4_pipeline_result.json`, `c14_autonomous_pipeline_result.json`,
`c14_1_autogpu_resume_result.json`, and `c14_1_autogpu_image_eval_summary.json`.

## `runtime/`

Runtime adapters and geometry/review helpers. Read `runtime/mask_tensor_adapter.py`
when debugging symbolic mask to binary control mask conversion.

## `schemas/`

Older and auxiliary schemas. Current Planner-facing schemas live under
`artifacts/current_interface/`.

## `scripts/`

Server run scripts, proxy helpers, and training command mirrors. Current training
mirrors include `c13_train_*.sh`, `c14_train_*_20.sh`, and C14.1 auto-GPU helpers.
Do not print local connection files used by server helpers.

## `server_configs/`

Server path templates. Filled local env files are sensitive and should not be
printed or committed.

## `tests/`

Protocol, schema, manifest, and validator regression tests. Run these before and
after modifying current schemas or examples.

## `third_party/`

Third-party references or placeholders. Do not edit or delete official source
checkouts as part of normal project work.

## `third_party_notices/`

License and provenance notices.

## `tools/`

Validators, converters, evaluators, reports, and inspection scripts. High-priority
current files: `validate_current_repairplan.py`,
`evaluate_c13_semantic_repair4_outputs.py`,
`convert_editroom_pair_to_semantic_layout.py`,
`search_valid_editroom_semantic_repair4_samples.py`, and
`replace_noop_c12_samples.py`.

## `vlm/`

VLM training/export helpers. For current Planner work, start with
`outputs/current_vlm_planner_handoff/` before code.

## If You Want To See Results First

Read `reports/c14_1_autogpu_resume_result.json`,
`reports/c14_1_autogpu_image_eval_summary.json`,
`docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md`, and
`outputs/manual_review/c14_1_autogpu_loss_curves/`.
