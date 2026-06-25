# C13 Semantic Repair4 Overfit

## Scope

This experiment trains only semantic_repair4 actions: ADD, REMOVE, TRANSLATE, and REPLACE. ROTATE and SCALE remain parametric_update actions and are excluded from Qwen/DiffSynth metadata.

## Data Gate

C12 was rerun after replacing no-op samples. Result: `C12_PASS` with 12 / 12 rows passing validator, oracle copyback, nonmask equality, palette validity, and no-op checks.

Dataset package:

- local path: `outputs/semantic_repair4_overfit_dataset_v1/`
- server path: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_overfit_dataset_v1/`
- metadata files: `metadata_add.csv`, `metadata_remove.csv`, `metadata_translate.csv`, `metadata_replace.csv`, `metadata_mixed.csv`
- DiffSynth loader dry-run: `PASS`

## Training

DiffSynth script: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`

Base model: `Qwen/Qwen-Image`

ControlNet: `DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint:model.safetensors`

All four single-action runs reached 100-step checkpoints. MIXED reached 108 recorded steps with `step-100.safetensors` saved.

## Step100 Evaluation

| Action | Steps | Gate | Masked Accuracy | Action IoU | Object Count F1 | Edit Success Rate |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| ADD | 100 | SINGLE_ACTION_PARTIAL | 0.3425 | 0.3333 | 0.3765 | 0.0000 |
| REMOVE | 100 | SINGLE_ACTION_PARTIAL | 0.7347 | 0.7347 | 0.7167 | 0.3333 |
| TRANSLATE | 100 | SINGLE_ACTION_PARTIAL | 0.6659 | 0.3333 | 0.6329 | 0.0000 |
| REPLACE | 102 | SINGLE_ACTION_PARTIAL | 0.6296 | 0.6667 | 0.7879 | 0.0000 |
| MIXED | 108 | MIXED_PARTIAL | 0.6135 | 0.6576 | 0.8317 | 0.1667 |

## Decision

The data, loader, and training-script gates passed. The model-level overfit gates did not pass: all single-action runs are PARTIAL, and MIXED is PARTIAL. Do not proceed to larger semantic_repair4 training yet.

The next step is targeted diagnosis of allowed-label violations, extra components, and palette adherence, followed by a focused 300-step continuation only after the evaluator/postprocess policy is confirmed.

## C14 Follow-up

C14 moved beyond the C13 3-row/action setting and built a medium diagnostic dataset with 20 rows per semantic_repair4 action. The medium data gate and DiffSynth `UnifiedDataset` dry-run passed. Medium training did not complete because the server GPU selected for REMOVE smoke did not have enough available memory; this is an environment blocker rather than a C13 data or loader regression.

See `docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md` and `reports/c14_autonomous_pipeline_result.json`.

## Artifacts

- training summary: `reports/c13_semantic_repair4_100step_training_summary.json`
- pipeline result: `reports/c13_semantic_repair4_pipeline_result.json`
- metrics: `reports/c13_overfit_ADD.json`, `reports/c13_overfit_REMOVE.json`, `reports/c13_overfit_TRANSLATE.json`, `reports/c13_overfit_REPLACE.json`, `reports/c13_overfit_MIXED.json`
- visual review: `outputs/manual_review/c13_overfit_ADD/step100_eval/`, `outputs/manual_review/c13_overfit_REMOVE/step100_eval/`, `outputs/manual_review/c13_overfit_TRANSLATE/step100_eval/`, `outputs/manual_review/c13_overfit_REPLACE/step100_eval/`, `outputs/manual_review/c13_overfit_MIXED/step100_eval/`
