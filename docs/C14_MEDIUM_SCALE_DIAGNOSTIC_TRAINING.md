# C14 Medium-Scale Diagnostic Training

## Status

C14 advanced through data construction and DiffSynth loader validation, then stopped at the training smoke because the available A800 GPU memory was not sufficient to load Qwen/DiffSynth. This is classified as `ENV_FAIL`, not a data, loader, or protocol failure.

## Current Protocol

- Planner-facing actions: ADD / REMOVE / TRANSLATE / ROTATE / SCALE / REPLACE
- semantic_repair4: ADD / REMOVE / TRANSLATE / REPLACE
- parametric_update: ROTATE / SCALE

ROTATE and SCALE remain structured parametric actions and are excluded from Qwen/DiffSynth semantic repair metadata.

## C13 Preflight

C13 small overfit produced PARTIAL gates for ADD, REMOVE, TRANSLATE, REPLACE, and MIXED. The runs reached checkpoints and showed learning signal, but strict edit gates were not met because outputs still had allowed-label violations, extra components, or incomplete target-region reconstruction.

See `reports/c14_preflight_c13_review.json`.

## Medium Dataset

- Dataset root: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v1/`
- Candidate source: `/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/test_dataset`
- Rows: ADD 20, REMOVE 20, TRANSLATE 20, REPLACE 20, total 80
- Data gate: `C14_DATA_PASS`
- Manual review: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/manual_review/c14_medium_dataset_preview/`

Filters used:

- current action only: ADD / REMOVE / TRANSLATE / REPLACE
- execution mode: semantic_repair
- binary control mask
- non-null source/target category fields where required
- changed pixels inside mask greater than 32
- changed ratio inside mask greater than 0.005
- oracle copyback pass
- nonmask equality pass
- palette validity pass
- no no-op rows
- no ROTATE/SCALE rows

## Metadata And Loader

DiffSynth metadata uses:

- `image` = I_target
- `blockwise_controlnet_image` = I_bad
- `blockwise_controlnet_inpaint_mask` = binary control_mask
- `prompt` = correction_prompt

True DiffSynth `UnifiedDataset` dry-run status: `PASS`. Each action metadata file loaded 512x512 RGB images and binary masks with unique values `[0, 255]`; prompts were loaded.

Reports:

- `reports/c14_medium_dataset_manifest.json`
- `reports/c14_medium_data_gate.json`
- `reports/c14_medium_data_distribution.json`
- `reports/c14_diffsynth_loader_dryrun.json`

## Training Configuration

- DiffSynth train script: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`
- UnifiedDataset: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/diffsynth/core/data/unified_dataset.py`
- Base model root: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models`
- ControlNet: `DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint:model.safetensors`
- Output root: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/`
- Config root: `/wuqingyaoa800/qiuziyan/LoReflection/configs/c14_semantic_repair4_medium/`
- Script root: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v1/_scripts/`
- Local config mirrors: `configs/c14_semantic_repair4_medium/`
- Local script mirrors: `scripts/c14_train_remove_20.sh`, `scripts/c14_train_replace_20.sh`, `scripts/c14_train_translate_20.sh`, `scripts/c14_train_add_20.sh`, `scripts/c14_train_mixed_80.sh`

Hyperparameters explicitly set in generated scripts/configs:

- batch size: 1
- learning rate: 1e-4
- LoRA rank: 32
- max pixels: 262144
- num workers: 0
- seed: 4411
- gradient checkpointing: enabled
- optimizer / scheduler / precision: DiffSynth defaults unless explicitly set by `train.py`

## Training Attempt

Training order was planned as REMOVE, REPLACE, TRANSLATE, ADD. REMOVE was attempted first.

- Primary script: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v1/_scripts/c14_train_remove.sh`
- Low-memory retry: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v1/_scripts/c14_train_remove_lowmem.sh`
- Primary log: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/REMOVE/logs/train.log`
- Low-memory log: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/REMOVE_LOW_MEM/logs/train.log`

Both attempts failed with CUDA out-of-memory before completing any training step. The low-memory retry still failed during model placement. `nvidia-smi` and the OOM traces showed hidden/unavailable processes occupying the selected GPU memory, and they were not visible to the current user, so no process was killed.

## Medium Training Gates

- REMOVE: ENV_FAIL before step 1
- REPLACE: skipped because REMOVE smoke failed due environment
- TRANSLATE: skipped because REMOVE smoke failed due environment
- ADD: skipped because REMOVE smoke failed due environment
- MIXED_80: skipped because single-action medium smoke did not complete
- 50/action expansion: skipped because 20/action training did not run

## Failure Analysis

- DATA_FAIL: none blocking; 80/80 samples passed the medium data gate
- LOADER_FAIL: none; DiffSynth `UnifiedDataset` dry-run passed
- TRAINING_FAIL: not reached because no training step completed
- EVAL_FAIL: not reached for C14 medium training
- SANITIZER_FAIL: none at data gate
- PROMPT_FAIL: not evaluated because training blocked
- MASK_FAIL: none at data/loader gate
- CATEGORY_FAIL: not evaluated in training; note that many REPLACE rows are same-semantic-category asset swaps with visible footprint or size changes
- ENV_FAIL: GPU memory unavailable for Qwen/DiffSynth medium smoke

## Decision

C14 is ready on the data and loader side, but medium training is blocked by environment. Do not expand to 50/action and do not start larger semantic_repair4 training until the 20/action REMOVE smoke completes on a GPU with enough free memory.

Exact next action: rerun C14 REMOVE 20-step smoke on a clear GPU using the generated dataset and scripts, then continue REPLACE, TRANSLATE, and ADD in order.

## C14.1 Auto-GPU Resume

C14.1 reran the medium diagnostic training with automatic GPU selection instead of a fixed GPU.

- selected GPU: GPU2, A800 class, 81219 MiB free at audit time
- memory probe: PROBE_PASS on REMOVE one-row training probe
- config: LoRA rank 32, max_pixels 262144, batch size 1, gradient checkpointing enabled
- semantic repair actions trained: ADD, REMOVE, TRANSLATE, REPLACE
- parametric actions excluded from Qwen/DiffSynth metadata: ROTATE, SCALE

Training completed:

| Action | Steps | Checkpoints | Peak allocated memory |
| --- | ---: | --- | ---: |
| REMOVE | 300 | step-100 / step-200 / step-300 | about 60682 MiB |
| REPLACE | 300 | step-100 / step-200 / step-300 | about 60693 MiB |
| TRANSLATE | 300 | step-100 / step-200 / step-300 | about 60694 MiB |
| ADD | 300 | step-100 / step-200 / step-300 | about 60691 MiB |
| MIXED_80 | 320 | step-100 / step-200 / step-300 / step-320 | about 60694 MiB |

Reports and artifacts:

- `reports/c14_1_autogpu_memory_audit.json`
- `reports/c14_1_autogpu_memory_probe_remove.json`
- `reports/c14_1_autogpu_resume_result.json`
- `reports/c14_1_autogpu_image_eval_summary.json`
- `outputs/manual_review/c14_1_autogpu_loss_curves/`
- remote checkpoints under `/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/`
- remote visual review outputs under `/wuqingyaoa800/qiuziyan/LoReflection/outputs/manual_review/c13_overfit_*/c14_1_autogpu_*_step300_eval/`

Image evaluation status:

- sampled step-300 eval ran for each single action and MIXED_80
- nonmask equality after copyback: 1.0
- snapped palette validity: 1.0
- edit_success: 0 on sampled rows
- main observed issue: high allowed-label violation counts and zero masked pixel accuracy

Decision after C14.1: training stability is no longer blocked by GPU memory, but output quality is not ready for 50/action expansion. The next step is to diagnose prompt/mask/evaluator behavior around allowed labels and target-region reconstruction.

## C14.2 Training-Inference Contract Diagnosis

C14.2 investigated why C14.1 training loss became very low while sampled image evaluation still reported zero edit success.

Key result:

- Primary root cause: `PALETTE_CONTRACT_FAIL causing EVAL_FAIL`
- Current frozen palette source: `artifacts/semantic_registry_v2/palette_frozen.json`
- Audited C14 medium semantic PNGs are not encoded with that frozen palette exactly.
- A representative REMOVE sample had `I_target_exact_palette_ratio = 0.0` and `I_bad_exact_palette_ratio = 0.0` against the frozen palette.
- The same sample still had valid mask/data geometry: binary mask values, `changed_pixels_inside_mask = 1419`, `mask_area_px = 2891`, and outside-mask equality between `I_bad` and `I_target`.

This explains the contradiction: even `I_target` or oracle-copyback predictions fail the current evaluator, because the evaluator snaps predictions to `palette_frozen.json` and then compares against unsnapped target RGB from a different palette encoding.

C14.2 decision:

- Do not continue 600/1000-step training.
- Do not expand to 50/action.
- Do not run larger semantic_repair4 training.
- Fix or regenerate C14 semantic_repair4 images so `I_bad` and `I_target` use `artifacts/semantic_registry_v2/palette_frozen.json` exactly, then rerun C14 data gate with exact palette validation and rerun evaluator self-test.

Reports:

- `reports/c14_2_training_inference_contract_result.json`
- `reports/c14_2_palette_contract_check.json`
- `reports/c14_2_evaluator_selftest.json`
- `reports/c14_2_metadata_contract_check.json`
- `reports/c14_2_palette_sanitizer_impact.json`
- `docs/C14_2_TRAINING_INFERENCE_CONTRACT_DIAGNOSIS.md`
- `docs/C14_2_FAILURE_DIAGNOSIS.md`

## C14.3 Palette-Fixed Clean Rerun Status

C14.3 repaired the C14 medium data contract by regenerating a v2 palette-fixed
dataset:

```text
outputs/semantic_repair4_medium_dataset_v2_palette_fixed/
```

The repair uses deterministic label-level mapping from the old SemLayoutDiff
native palette to `artifacts/semantic_registry_v2/palette_frozen.json`. It does
not change taxonomy, semantic registry, frozen palette, or action protocol.

Current C14.3 gates:

- exact palette data gate: `C14_3_DATA_PASS`
- evaluator self-test: `EVAL_OK`
- DiffSynth loader dry-run: `LOADER_PASS`
- old C14.1 checkpoints: retained for audit but invalidated as model-quality evidence

The full evaluator self-test now passes for all 80 rows with `I_target` and
oracle copyback, while `I_bad` and random fixed-palette predictions fail as
expected.

## C14.4 Palette-Fixed Clean Training Result

C14.4 selected GPU0 with 81219 MiB free and completed corrected fixed-step
training for REMOVE, REPLACE, TRANSLATE, and ADD at 300 steps each. All four
actions produced nonzero action-specific metrics, and MIXED_80 was therefore
run and evaluated at step 300.

REMOVE reached 0.60 sampled edit success and 0.914 action IoU. REPLACE,
TRANSLATE, ADD, and MIXED produced nonzero IoU but zero strict edit success.
The palette, evaluator, loader, and nonmask-copyback contracts passed.

The next step is C15 prompt/mask/action-specific diagnosis. Do not expand to
50/action yet.
