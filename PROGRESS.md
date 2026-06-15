# LoReflection Progress

## Completed

### Step 2.1 Local Interface Audit
Status: Completed

- Schema / validator / smoke test passed.
- Prompt Builder, Mask Tensor Adapter, Qwen-VL SFT export, and DiffSynth metadata export were checked.
- `tools/run_smoke_test.py` passed with:
  `LoReflection local smoke test passed.`

### Step 2.2 SemLayoutDiff Adapter
Status: Completed at toy level

- `tools/inspect_semlayoutdiff_outputs.py` completed.
- `tools/convert_semlayoutdiff_to_loreflection.py` completed.
- Toy SemLayoutDiff-like input was converted into:
  - Architecture JSON
  - Architecture condition image
  - GT semantic layout
  - conversion report
- `validate_all --strict` passed.
- No schema change was required.

Current interpretation:
This means the SemLayoutDiff adapter interface is ready at toy level. It does not mean that real 3D-FRONT / 3D-FUTURE data has been fully connected.

## Current TODO

### Server-side SemLayoutDiff / 3D-FRONT TODO
- Confirm real SemLayoutDiff `.npy` / pickle / JSON field names.
- Map real 3D-FRONT room metadata to LoReflection Architecture JSON.
- Map boundary, door, window, clearance, and coordinate transforms.
- Map real SemLayoutDiff semantic layout channels / categories to `configs/palette_v1.json`.
- Convert SemLayoutDiff sampled layout outputs into LoReflection eval representation.
- Configure server paths:
  - `SEMLAYOUTDIFF_ROOT`
  - `THREED_FRONT_ROOT`
  - `THREED_FUTURE_ROOT`
  - `OUTPUT_ROOT`

## Next Step

### Step 2.3 EditRoom Adapter
Status: Completed at toy level

Purpose:
Convert EditRoom-like editing pairs into LoReflection Planner SFT and DiffSynth repair samples.

- `tools/inspect_editroom_outputs.py` completed.
- `tools/convert_editroom_to_loreflection.py` completed.
- Toy EditRoom-like before/after pair was converted into:
  - mask_spec
  - binary control_mask
  - RepairPlan
  - Planner SFT manifest
  - ControlNet / DiffSynth repair manifest
  - conversion report
- `validate_all --strict` passed.

Current interpretation:
This means the EditRoom adapter interface is ready at toy level. It does not mean that real EditRoom data, real 3D-FRONT / 3D-FUTURE data, or real EditRoom model outputs have been fully connected.

### Step 2.3R Regression Audit
Status: Completed

Purpose:
Verify that Step 2.3 schema/runtime changes did not break Step 2.1 and Step 2.2, and decide whether the current toy-level interface can be frozen.

Regression commands:
- `examples/toy_samples` strict validation: PASS
- local smoke test: PASS
- SemLayoutDiff toy output strict validation: PASS
- EditRoom toy output strict validation: PASS
- Qwen-VL export check: PASS
- DiffSynth export check: PASS

Interface consistency:
- mask_spec schema/runtime mismatch: no
- RepairPlan schema/adapter mismatch: no
- ControlNet/DiffSynth mapping mismatch: no
- Qwen-VL SFT format issue: no
- Absolute path violation: no

Canonical tags:
- Step 2.2: `step2.2-semlayoutdiff-toy-pass`
- Step 2.3: `step2.3-editroom-toy-pass-v2`

Result:
- Recommended interface status: frozen at toy level.
- Freeze tag: `interface-freeze-v1`

### Step 2.4 Unified Toy Package + Server Dry-run
Status: Completed

Purpose:
Create a unified toy-level LoReflection data package and server path dry-run utilities after `interface-freeze-v1`.

Inputs:
- `examples/toy_samples`
- `outputs/semlayoutdiff_toy_loreflection`
- `outputs/editroom_toy_loreflection`

Outputs:
- `outputs/unified_toy_package_v1`
- `server_configs/paths.template.env`
- `docs/SERVER_DRY_RUN.md`
- `reports/server_path_check_report.json`

Validation:
- unified toy package build: PASS
- unified toy package strict validation: PASS
- server path dry-run with template env: PASS

Next development task:
After the unified toy package and server dry-run pass, prepare Step 3 server-side val50 construction.

Important restriction:
Do not connect real 3D-FRONT / 3D-FUTURE, download model weights, or start training during Step 2.4.

### Step 3.0 Pazhou Server Onboarding
Status: Completed

Purpose:
Prepare sanitized server-side path templates and dry-run scripts for Pazhou A800 / 3090 without committing SSH secrets or starting training.

Safety:
- No passwords committed.
- No model or data downloaded.
- No training started.
- No real 3D-FRONT conversion started.

Validation:
- `tools/check_no_secrets.py --strict`: PASS
- Pazhou path template dry-run: PASS
- Pazhou real source inspection template dry-run: PASS

### Step 3.2A Dataset Provenance Gap Analysis
Status: Completed

Purpose:
Document that the current server bundle is official-like but EditRoom-provided, and freeze safe wording before converter prototype work.

Result:
- Current data source wording: `EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle`.
- Allowed for converter prototype, field mapping, val50 prototype, and LoReflection pipeline debugging.
- Not to be described as a freshly downloaded official raw archive.
- Final main experiments require official raw bundle verification or explicit provenance disclosure.
- No data download, model download, training, or full conversion was performed.

