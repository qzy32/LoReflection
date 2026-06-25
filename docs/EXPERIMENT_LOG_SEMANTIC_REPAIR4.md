# Experiment Log Semantic Repair4

## Run Date

2026-06-21

## Current Protocol

semantic_repair4 contains ADD, REMOVE, TRANSLATE, and REPLACE. parametric_update contains ROTATE and SCALE. ROTATE and SCALE were not included in Qwen/DiffSynth metadata or training.

## Server

- server work root: `/wuqingyaoa800/qiuziyan`
- LoReflection path: `/wuqingyaoa800/qiuziyan/LoReflection`
- DiffSynth path: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio`
- Python env: `/wuqingyaoa800/qiuziyan/envs/diffsynth-qwen`
- GPU usage: GPU2 was used for inference and MIXED training; GPU3 had a stale compute context after previous runs.

## Dataset

- dataset path: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_overfit_dataset_v1/`
- rows: ADD 3, REMOVE 3, TRANSLATE 3, REPLACE 3, MIXED 12
- loader dry-run: `PASS`

## Training Commands

The run used DiffSynth `examples/qwen_image/model_training/train.py` with `image`, `blockwise_controlnet_image`, and `blockwise_controlnet_inpaint_mask` data keys, LoRA rank 32, learning rate 1e-4, max pixels 262144, batch size 1, and fixed seeds.

## Runs

| Run ID | Action | Seed | Rows | Steps | Best Checkpoint | Gate |
| --- | --- | ---: | ---: | ---: | --- | --- |
| c13_add_100 | ADD | fixed | 3 | 100 | `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_overfit_v1/ADD/run_100steps/step-100.safetensors` | SINGLE_ACTION_PARTIAL |
| c13_remove_100 | REMOVE | fixed | 3 | 100 | `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_overfit_v1/REMOVE/run_100steps/step-100.safetensors` | SINGLE_ACTION_PARTIAL |
| c13_translate_100 | TRANSLATE | fixed | 3 | 100 | `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_overfit_v1/TRANSLATE/run_100steps/step-100.safetensors` | SINGLE_ACTION_PARTIAL |
| c13_replace_100 | REPLACE | fixed | 3 | 102 | `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_overfit_v1/REPLACE/run_100steps/step-100.safetensors` | SINGLE_ACTION_PARTIAL |
| c13_mixed_100 | MIXED | 5311 | 12 | 108 | `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_overfit_v1/MIXED/run_100steps/step-100.safetensors` | MIXED_PARTIAL |

## Curves And Metrics

- loss curves: `reports/c13_loss_curve_ADD.png`, `reports/c13_loss_curve_REMOVE.png`, `reports/c13_loss_curve_TRANSLATE.png`, `reports/c13_loss_curve_REPLACE.png`, `reports/c13_loss_curve_MIXED.png`
- metrics JSON/CSV: `reports/c13_overfit_ADD.*`, `reports/c13_overfit_REMOVE.*`, `reports/c13_overfit_TRANSLATE.*`, `reports/c13_overfit_REPLACE.*`, `reports/c13_overfit_MIXED.*`
- visual folders: `outputs/manual_review/c13_overfit_*/step100_eval/`

## Failure Analysis

Data and loader gates passed. Training produced checkpoints for all runs. Strict overfit gates failed because outputs still contain allowed-label violations, extra components, and incomplete target-region reconstruction after palette snapping and copyback.

## Decision Gate

- larger semantic_repair4 training: no
- VLM Planner small-scale SFT smoke: yes, interface side remains usable
- next action: diagnose output sanitization and allowed-label policy before any longer Qwen/DiffSynth run

## C14 Medium Diagnostic Attempt

### Dataset

- run id: c14_medium_dataset_v1
- dataset path: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v1/`
- candidate source: `/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/test_dataset`
- rows: ADD 20, REMOVE 20, TRANSLATE 20, REPLACE 20, MIXED_80 80
- data gate: C14_DATA_PASS
- loader dry-run: PASS with DiffSynth `UnifiedDataset`

### Training Attempt

| Run ID | Action | Seed | Rows | Steps | Status | Artifacts |
| --- | --- | ---: | ---: | ---: | --- | --- |
| c14_remove_20_smoke | REMOVE | 4411 | 20 | 0 | ENV_FAIL: CUDA out of memory before step 1 | `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/REMOVE/logs/train.log` |
| c14_remove_20_lowmem | REMOVE | 4411 | 20 | 0 | ENV_FAIL: low-memory retry also ran out of GPU memory before step 1 | `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/REMOVE_LOW_MEM/logs/train.log` |

REPLACE, TRANSLATE, ADD, MIXED_80, and 50/action expansion were skipped because the first medium smoke did not complete. No checkpoint was produced.

### C14 Reports

- `docs/C14_MEDIUM_SCALE_DIAGNOSTIC_TRAINING.md`
- `reports/c14_autonomous_pipeline_result.json`
- `reports/c14_medium_dataset_manifest.json`
- `reports/c14_medium_data_gate.json`
- `reports/c14_diffsynth_loader_dryrun.json`

### C14 Decision Gate

- medium data construction: pass
- DiffSynth loader: pass
- medium training: blocked by server GPU memory
- next action: rerun REMOVE 20-step smoke on a GPU with enough free memory, then continue REPLACE, TRANSLATE, and ADD

## C14.1 Auto-GPU Resume

### Run Context

- date/time: 2026-06-21
- server: A800 host
- selected GPU: GPU2
- selection reason: largest free memory at audit time, no active compute-app entry, A800 class GPU
- DiffSynth path: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio`
- LoReflection server path: `/wuqingyaoa800/qiuziyan/LoReflection`
- dataset path: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v1/`
- output root: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/`
- reports: `reports/c14_1_autogpu_resume_result.json`, `reports/c14_1_autogpu_image_eval_summary.json`

Current protocol remained unchanged. semantic_repair4 contains ADD, REMOVE, TRANSLATE, and REPLACE. parametric_update contains ROTATE and SCALE. ROTATE and SCALE were not included in DiffSynth metadata or semantic repair training.

### Hyperparameters

- model path root: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models`
- training script: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`
- batch size: 1
- learning rate: 1e-4
- LoRA rank: 32
- max pixels: 262144
- num workers: 0
- seed: 4411
- gradient checkpointing: enabled
- validation during training: disabled
- image generation during training: disabled

### Runs

| Run ID | Action | Seed | Rows | Steps | Best Checkpoint | Status |
| --- | --- | ---: | ---: | ---: | --- | --- |
| c14_1_probe_remove | REMOVE | 4411 | 1 | 1 | `autogpu_memory_probe/run/step-1.safetensors` | PROBE_PASS |
| c14_1_remove_300 | REMOVE | 4411 | 20 | 300 | `REMOVE_20/gpu2_rank32_300steps/run/step-300.safetensors` | trained |
| c14_1_replace_300 | REPLACE | 4411 | 20 | 300 | `REPLACE_20/gpu2_rank32_300steps/run/step-300.safetensors` | trained |
| c14_1_translate_300 | TRANSLATE | 4411 | 20 | 300 | `TRANSLATE_20/gpu2_rank32_300steps/run/step-300.safetensors` | trained |
| c14_1_add_300 | ADD | 4411 | 20 | 300 | `ADD_20/gpu2_rank32_300steps/run/step-300.safetensors` | trained |
| c14_1_mixed_320 | MIXED_80 | 4411 | 80 | 320 | `MIXED_80/gpu2_rank32_320steps/run/step-300.safetensors` and `step-320.safetensors` | trained |

### Curves And Evaluation

- loss curves: `outputs/manual_review/c14_1_autogpu_loss_curves/`
- training CSV/JSON: `reports/c14_1_autogpu_medium_*`
- image eval summary: `reports/c14_1_autogpu_image_eval_summary.json`
- remote visual folders: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/manual_review/c13_overfit_*/c14_1_autogpu_*_step300_eval/`

Step-300 sampled image evaluation:

- edit_success: 0 for ADD, REMOVE, TRANSLATE, REPLACE, and MIXED_80 sampled rows
- nonmask equality after copyback: 1.0
- snapped palette validity: 1.0
- main failure signal: high allowed-label violations and zero masked pixel accuracy

### Decision Gate

- can proceed to C14 medium mixed: completed to 320 steps
- can proceed to 50/action: no
- can proceed to larger semantic_repair4 training: no
- next action: diagnose prompt/mask/evaluator behavior around allowed-label violations and target-region reconstruction before any larger training.

## C14.2 Training-Inference Contract Diagnosis

### Run Context

- date/time: 2026-06-21
- server: A800 host for remote evidence; local repo for report consolidation
- purpose: diagnose low training loss versus failed sampled image evaluation
- protocol: unchanged; semantic_repair4 is ADD, REMOVE, TRANSLATE, REPLACE; ROTATE and SCALE remain parametric_update only

### Evidence

- C14.1 checkpoints exist for REMOVE, REPLACE, TRANSLATE, ADD, and MIXED_80.
- C14.1 sampled image eval reported edit_success 0 and masked_pixel_accuracy 0 on sampled rows.
- C14.2 evaluator self-test did not pass: `I_target` and oracle-copyback predictions also failed.
- C14.2 metadata contract check passed for paths, binary mask values, inside-mask changes, and outside-mask equality.
- Additional palette contract check found the blocking issue: C14 medium `I_bad` and `I_target` are not encoded in `artifacts/semantic_registry_v2/palette_frozen.json`.

Representative sample:

- sample: `remove_001_015ed8e0-35dc-41ab-9a9e-b3dbba4ec64a_MasterBedroom-33296_remove-0_0`
- `I_target_exact_palette_ratio`: 0.0
- `I_bad_exact_palette_ratio`: 0.0
- `target_equals_snapped_target_inside_mask_ratio`: 0.0
- `bad_equals_target_outside_mask_ratio`: 1.0
- `changed_pixels_inside_mask`: 1419
- `mask_area_px`: 2891

### Decision Gate

- primary failure class: `PALETTE_CONTRACT_FAIL causing EVAL_FAIL`
- training continuation: blocked
- 50/action expansion: blocked
- larger semantic_repair4 training: blocked
- next action: regenerate or adapt C14 semantic_repair4 samples so `I_bad` and `I_target` use the current frozen palette exactly, then rerun data gate and evaluator self-test before any further training.

### Artifacts

- `reports/c14_2_training_inference_contract_result.json`
- `reports/c14_2_palette_contract_check.json`
- `reports/c14_2_evaluator_selftest.json`
- `reports/c14_2_metadata_contract_check.json`
- `reports/c14_2_palette_sanitizer_impact.json`
- `reports/c14_2_per_category_failure_diagnosis.json`
- `docs/C14_2_TRAINING_INFERENCE_CONTRACT_DIAGNOSIS.md`
- `docs/C14_2_FAILURE_DIAGNOSIS.md`

## C14.3 Palette Contract Repair

### Run Context

- date/time: 2026-06-21
- server: A800 host for dataset regeneration and evaluator self-test
- purpose: repair the palette contract before drawing any model-quality conclusion
- protocol: unchanged; semantic_repair4 is ADD, REMOVE, TRANSLATE, REPLACE; ROTATE and SCALE remain parametric_update only

### Data Repair

- source dataset: `outputs/semantic_repair4_medium_dataset_v1/`
- repaired dataset: `outputs/semantic_repair4_medium_dataset_v2_palette_fixed/`
- strategy: SemLayoutDiff native RGB -> semantic label -> frozen RGB
- frozen palette: `artifacts/semantic_registry_v2/palette_frozen.json`
- rows: 80 total, 20 per action

### Gates

- data gate: `C14_3_DATA_PASS`
- evaluator self-test: `EVAL_OK`
- loader dry-run: `LOADER_PASS`
- allowed-label policy: repaired by adding all frozen semantic ids present in `I_target` inside the white mask

### Training Status

Clean palette-fixed training is ready but deferred by GPU availability. Current
A800 audit found no GPU with at least 60000 MiB free memory. The wait-and-run
entry point is:

```bash
bash scripts/c14_3_wait_and_run_palette_fixed.sh
```

### Artifacts

- `reports/c14_3_palette_contract_audit.json`
- `reports/c14_3_palette_fixed_data_gate.json`
- `reports/c14_3_evaluator_selftest_palette_fixed.json`
- `reports/c14_3_diffsynth_loader_dryrun_palette_fixed.json`
- `reports/c14_3_palette_contract_repair_result.json`
- `docs/C14_3_PALETTE_CONTRACT_REPAIR_AND_RERUN.md`

## C14.4 Palette-Fixed Clean Training Run

### Run Context

- date/time: 2026-06-22 Asia/Shanghai
- server: A800 host
- purpose: run the first valid palette-fixed C14 medium training and evaluation
- protocol: unchanged; semantic_repair4 is ADD, REMOVE, TRANSLATE, REPLACE

### Gate

- current validator: PASS
- current protocol tests: PASS
- palette-fixed data gate: `C14_3_DATA_PASS`
- evaluator self-test: `EVAL_OK`
- loader dry-run: `LOADER_PASS`

### Executor

- script: `scripts/c14_4_wait_and_run_palette_fixed_clean_training.sh`
- policy: prefer 60000 MiB free memory, allow a lower-memory fallback
- final status: `COMPLETE_WITH_MIXED`
- report: `reports/c14_4_palette_fixed_clean_training_result.json`

## C14.4 Final Result

- selected GPU: GPU0, NVIDIA A800-SXM4-80GB
- free memory at selection: 81219 MiB
- corrected run tag: `c14_4_fixedsteps`
- REMOVE: 300 steps, loss 0.000496, edit success 0.60, action IoU 0.914
- REPLACE: 300 steps, loss 0.001729, action IoU 0.611
- TRANSLATE: 300 steps, loss 0.002111, action IoU 0.683
- ADD: 300 steps, loss 0.002530, action IoU 0.806
- MIXED_80: step-300 evaluation, loss 0.002473, action IoU 0.800

All runs had snapped palette validity 1.0 and nonmask equality 1.0. All four
single actions produced nonzero action-specific signals, so the mixed gate
passed. Only REMOVE produced nonzero strict sampled edit success.

Decision: proceed to C15 prompt/mask/action-specific ablations. Do not expand
to 50/action or larger semantic_repair4 training yet.
