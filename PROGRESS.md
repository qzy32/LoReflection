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

### Step 2.4 Server Data Mapping
Next development task:
After SemLayoutDiff and EditRoom adapters are both ready at toy level, map real server-side data fields into the local LoReflection contracts.

Important restriction:
Do not connect real 3D-FRONT / 3D-FUTURE before Step 2.3 is completed. Real data integration will be handled after SemLayoutDiff and EditRoom adapters are both ready at toy level.
