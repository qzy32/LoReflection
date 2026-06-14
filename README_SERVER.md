# LoReflection Server Workflow

Server runs are responsible for real model and dataset work. Local code only prepares schemas, manifests, toy validation, and conversion scripts.

Real server-side data conversion should start only after `interface-freeze-v1` is created. Before that, do not run real 3D-FRONT / 3D-FUTURE conversion or model training.

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

## Baselines

InstantX/Qwen-Image-ControlNet-Inpainting is reserved as a zero-shot executor baseline. Do not use it as the main training path unless the experiment plan changes.
