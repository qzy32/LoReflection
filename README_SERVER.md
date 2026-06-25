# LoReflection Server Workflow

Server runs are responsible for real model and dataset work. Local code only prepares schemas, manifests, toy validation, and conversion scripts.

Real server-side data conversion should start only after `interface-freeze-v1` is created. Before that, do not run real 3D-FRONT / 3D-FUTURE conversion or model training.

## Pazhou Server Setup

Use the sanitized Pazhou template:

```bash
cp server_configs/paths.pazhou.template.env server_configs/paths.local.env
# edit paths.local.env on the server
bash scripts/server_step3_dryrun_pazhou.sh
```

Do not commit:

- `paths.local.env`
- SSH guide files
- credentials
- model weights
- datasets

Recommended work roots:

- A800: `/wuqingyaoa800/qiuziyan`
- 3090: `/wuqingyao/custom_home/qiuziyan`

Do not use `/home` for projects, model weights, datasets, logs, or large outputs. Current A800 usage is a direct SSH workflow, not a default Slurm workflow; do not assume `sbatch`, `salloc`, or `sinfo` as the normal path.

## Server Dry-run

Before running real data conversion or training, copy:

```text
server_configs/paths.template.env
```

to:

```text
server_configs/paths.local.env
```

then fill real server paths and run:

```bash
python tools/check_server_paths.py \
  --env-file server_configs/paths.local.env \
  --report reports/server_path_check_report.json
```

## Paths To Configure

- `/server/path/to/3D-FRONT`
- `/server/path/to/3D-FUTURE`
- `/server/path/to/qwen-vl-finetune`
- `/server/path/to/Qwen2.5-VL`
- `/server/path/to/Qwen-Image`
- `/server/path/to/DiffSynth-Studio`
- `/server/path/to/InstantX/Qwen-Image-ControlNet-Inpainting`
- `/server/path/to/data/loreflection_diffsynth_inpaint`
- `/server/path/to/outputs/...`

## VLM SFT

Use local `tools/export_to_qwenvl_sft.py` output as the `image + conversations` file for qwen-vl-finetune. The three task roles should be separated by prompt tags:

- `[TARGET_STATE_CONSTRUCTION]`
- `[SEMANTIC_REVIEW]`
- `[CORRECTION_PLANNING_WITH_MASK_PLAN]`

The local template is `vlm/train_qwenvl_lora.sh`. Edit all `/server/path/...` entries before running.

## DiffSynth Inpaint LoRA

Use local `tools/export_loreflection_to_diffsynth_inpaint.py` to create:

```text
metadata.csv
image = target_image
blockwise_controlnet_image = control_image / I_bad
blockwise_controlnet_inpaint_mask = control_mask
prompt = correction_prompt
```

The local template is `diffusion/train_diffsynth_qwen_inpaint_lora.sh`. It is a server-only placeholder and may need adjustment to the exact DiffSynth-Studio script name/API available on the server.

Current semantic_repair4 training status: C12 now reports 12 / 12 passing ADD / REMOVE / TRANSLATE / REPLACE samples, and C13 small Qwen/DiffSynth overfit has completed through 100-step checkpoints plus a 12-row mixed run. The strict model gates are PARTIAL, so do not start larger semantic_repair4 training until the C13 output diagnosis is addressed.

C14.1 auto-GPU resume status: a clear A800 GPU was selected automatically, REMOVE / REPLACE / TRANSLATE / ADD each completed 300 training steps, and MIXED_80 completed 320 steps. Training stability is now verified.

C14.2 diagnosis status: step-300 image evaluation is blocked by a palette/evaluator contract failure. The C14 medium semantic PNGs are not encoded with `artifacts/semantic_registry_v2/palette_frozen.json` exactly, so even `I_target` and oracle-copyback evaluator self-tests fail. Use `reports/c14_2_training_inference_contract_result.json`, `reports/c14_2_palette_contract_check.json`, and `docs/C14_2_TRAINING_INFERENCE_CONTRACT_DIAGNOSIS.md` before any 600-step continuation or 50/action expansion.

C14.3 server status: the C14 medium dataset was regenerated as
`outputs/semantic_repair4_medium_dataset_v2_palette_fixed/` (server-side; not
expected in the local checkout) using exact frozen
palette RGBs. Data gate, evaluator self-test, and DiffSynth loader dry-run now
pass. The clean rerun is ready but currently waits for an A800 with at least
60000 MiB free memory. Use:

```bash
bash scripts/c14_3_wait_and_run_palette_fixed.sh
```

This script runs only semantic_repair4 actions: REMOVE, REPLACE, TRANSLATE, and
ADD. ROTATE and SCALE remain structured parametric_update actions and are not
included in DiffSynth metadata.

C14.4 final status: `COMPLETE_WITH_MIXED`. GPU0 was selected with 81219 MiB
free. The corrected `c14_4_fixedsteps` single-action runs completed at exactly
300 steps. MIXED_80 was evaluated at step 300 and ended its epoch at step 320.
Use `reports/c14_4_palette_fixed_clean_training_result.json` and
`docs/C14_4_PALETTE_FIXED_CLEAN_TRAINING_RESULT.md`.

## Baselines

InstantX/Qwen-Image-ControlNet-Inpainting is reserved as a zero-shot executor baseline. Do not use it as the main training path unless the experiment plan changes.

## Dataset Provenance

Current server-side prototype data should be described as:

```text
EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle
```

It is official-like and suitable for converter prototype / val50 prototype debugging, but it should not be described as a freshly downloaded official raw archive. Main experiments require official raw bundle verification or explicit provenance disclosure.
