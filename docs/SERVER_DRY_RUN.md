# Server Dry-run

## Purpose

The server dry-run checks whether the server-side LoReflection workspace is ready for real val50 / 1k data construction. It checks:

- third-party repository paths;
- data paths;
- model paths;
- output directory paths;
- whether the configured machine has the minimum path layout needed before real conversion or training.

## What It Does Not Do

The dry-run intentionally does not:

- download data;
- download models;
- start Qwen-VL training;
- start DiffSynth training;
- run real 3D-FRONT conversion;
- run real model inference.

## Required Server Paths

The path file should define:

- `LOREFLECTION_ROOT`
- `SEMLAYOUTDIFF_ROOT`
- `EDITROOM_ROOT`
- `DIFFSYNTH_ROOT`
- `QWEN_VL_REPO`
- `THREED_FRONT_ROOT`
- `THREED_FUTURE_ROOT`
- `QWEN25_VL_MODEL_PATH`
- `QWEN_IMAGE_MODEL_PATH`
- `DIFFSYNTH_INPAINT_MODEL_PATH`
- `INSTANTX_INPAINT_MODEL_PATH`
- `OUTPUT_ROOT`

## Recommended Order On Server

1. Clone LoReflection.
2. Clone or prepare SemLayoutDiff, EditRoom, DiffSynth-Studio, and qwen-vl-finetune.
3. Copy `server_configs/paths.template.env` to `server_configs/paths.local.env`.
4. Fill real paths.
5. Run `check_server_paths.py`.
6. Only then start real val50 data conversion.

```bash
python tools/check_server_paths.py \
  --env-file server_configs/paths.local.env \
  --report reports/server_path_check_report.json \
  --strict
```

Template placeholders are reported as warnings, not as proof that real server data is ready.
