# LoReflection

Local skeleton for the AAAI LoReflection project: a closed-loop indoor semantic layout generation and repair system built around Goal/Observed LoState, LoReview, RepairPlan, VLM mask planning, and binary ControlNet inpainting masks.

This repository is intentionally local-only at this stage. It creates schemas, validators, converters, prompt/mask utilities, and toy examples. It does not download model weights, download 3D-FRONT/3D-FUTURE, or run real training.

## Current Development Stage

The project is currently in the local interface and adapter construction stage.

Completed:
- Step 2.1 local interface audit and smoke test.
- Step 2.2 SemLayoutDiff adapter toy-level conversion.
- Step 2.3 EditRoom adapter toy-level conversion.
- Step 2.4 unified toy package and server dry-run preparation.

Not yet completed:
- Real 3D-FRONT / 3D-FUTURE conversion.
- Real SemLayoutDiff output parsing.
- Real EditRoom output parsing.
- Qwen-VL training.
- DiffSynth Qwen-Image inpainting training.
- Closed-loop main experiments.

Next:
- Step 3 server-side val50 construction.

## Interface Freeze Status

Current toy-level interface status:
- Step 2.1 local interface audit: passed
- Step 2.2 SemLayoutDiff adapter: passed
- Step 2.3 EditRoom adapter: passed
- Step 2.3R regression audit: passed

The toy-level interface can be treated as frozen only if Step 2.3R passes.

Current recommendation:
- Frozen at toy level under `interface-freeze-v1`.

## Step 2.4 Unified Toy Package

After `interface-freeze-v1`, the project builds a unified toy package that simulates the future val50 / 1k data layout without using real data or model weights.

```bash
python tools/build_unified_toy_package.py \
  --toy-root examples/toy_samples \
  --semlayoutdiff-root outputs/semlayoutdiff_toy_loreflection \
  --editroom-root outputs/editroom_toy_loreflection \
  --output-root outputs/unified_toy_package_v1 \
  --mode toy

python tools/validate_unified_toy_package.py \
  --package-root outputs/unified_toy_package_v1 \
  --strict \
  --report outputs/unified_toy_package_v1/reports/unified_package_validation_report.json
```

Server path dry-run:

```bash
python tools/check_server_paths.py \
  --env-file server_configs/paths.template.env \
  --report reports/server_path_check_report.json
```

## Local Setup

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
```

## Main Local Flow

1. Build or import `Architecture JSON`.
2. Build a toy or server-produced `Goal LoState`.
3. Compile a `Prompt Package` with `runtime/prompt_builder.py`.
4. Render toy semantic images locally only for smoke tests.
5. Observe fixed-palette semantic maps with `runtime/observer.py`.
6. Build `LoReview` with local Track-A plus placeholder Track-B.
7. Convert `RepairPlan.mask_spec` to a binary `control_mask` with `runtime/mask_tensor_adapter.py`.
8. Export Planner SFT data for qwen-vl-finetune.
9. Export repair pairs to DiffSynth `metadata.csv`.

## Smoke Test

From the repository root:

```bash
python tools/validate_all.py --data-root examples/toy_samples
python data_pipeline/render_arch_condition.py --architecture examples/toy_samples/architecture_v1.json --output examples/toy_samples/arch_condition.png
python data_pipeline/render_gt_semantic_layout.py --goal-lostate examples/toy_samples/goal_lostate_v1.json --output examples/toy_samples/target_layout.png
python data_pipeline/generate_perturbations.py --input-image examples/toy_samples/target_layout.png --output-image examples/toy_samples/bad_layout.png --manifest examples/toy_samples/perturbations.json
python data_pipeline/build_observed_lostate.py --image examples/toy_samples/bad_layout.png --architecture examples/toy_samples/architecture_v1.json --output examples/toy_samples/observed_from_image.json
python data_pipeline/build_loreview.py --goal-lostate examples/toy_samples/goal_lostate_v1.json --observed-lostate examples/toy_samples/observed_from_image.json --output examples/toy_samples/loreview_from_image.json
python runtime/mask_tensor_adapter.py --mask-spec examples/toy_samples/mask_spec_v1.json --control-image examples/toy_samples/bad_layout.png --output examples/toy_samples/control_mask.png
python data_pipeline/build_controlnet_repair_pairs.py --target-image examples/toy_samples/target_layout.png --control-image examples/toy_samples/bad_layout.png --control-mask examples/toy_samples/control_mask.png --repairplan examples/toy_samples/repairplan_v1.json --output examples/toy_samples/controlnet_repair_v1/train.json
python tools/export_loreflection_to_diffsynth_inpaint.py --input examples/toy_samples/controlnet_repair_v1/train.json --output-dir outputs/diffsynth_toy --mode copy
python tools/export_to_qwenvl_sft.py --input examples/toy_samples/planner_sft_manifest.json --output outputs/qwenvl_sft_toy.json
```

Or run the whole local pipeline at once:

```bash
python tools/run_smoke_test.py
```

## Step 2.2 SemLayoutDiff Adapter

SemLayoutDiff is used as a third-party preprocessing reference and architecture-conditioned semantic layout baseline source. It is not the LoReflection main method, and local adapter tests do not download 3D-FRONT, 3D-FUTURE, Blender assets, model weights, or start training.

Inspect an optional SemLayoutDiff checkout and the local toy sample:

```bash
python tools/inspect_semlayoutdiff_outputs.py \
  --semlayoutdiff-root third_party/SemLayoutDiff \
  --sample-dir examples/toy_semlayoutdiff \
  --report experiments/val50/semlayoutdiff_inspect_report.json
```

Convert the toy SemLayoutDiff-like sample into LoReflection artifacts:

```bash
python tools/convert_semlayoutdiff_to_loreflection.py \
  --input-root examples/toy_semlayoutdiff \
  --output-root outputs/semlayoutdiff_toy_loreflection \
  --palette configs/palette_v1.json \
  --mode toy
```

See `docs/SEMLAYOUTDIFF_ADAPTER.md` for server path placeholders and real-data TODOs.

## Step 2.3 EditRoom Adapter

EditRoom is used as an editing pair, perturbation, and editing baseline source. It is not the LoReflection main method. The local adapter converts toy EditRoom-like before/after pairs into Planner SFT manifests and ControlNet / DiffSynth repair samples.

Inspect an optional EditRoom checkout and the local toy sample:

```bash
python tools/inspect_editroom_outputs.py \
  --editroom-root third_party/EditRoom \
  --sample-dir examples/toy_editroom \
  --report experiments/val50/editroom_inspect_report.json
```

Convert the toy EditRoom-like pair into LoReflection training artifacts:

```bash
python tools/convert_editroom_to_loreflection.py \
  --input-root examples/toy_editroom \
  --output-root outputs/editroom_toy_loreflection \
  --mode toy
```

See `docs/EDITROOM_ADAPTER.md` for mapping details and server-side TODOs.

## Key Files

- `schemas/`: minimal JSON Schemas for Architecture, Goal/Observed LoState, Prompt Package, LoReview, RepairPlan, mask_spec, ControlNet sample, and eval representation.
- `runtime/prompt_builder.py`: rule-based Prompt Compiler.
- `runtime/mask_tensor_adapter.py`: converts bbox, polygon, and instance_ref mask specs to binary masks.
- `data_pipeline/render_arch_condition.py`: PIL-based top-down architecture renderer, no Blender required.
- `tools/export_to_qwenvl_sft.py`: converts Planner SFT manifests to Qwen-VL `image + conversations`.
- `tools/export_loreflection_to_diffsynth_inpaint.py`: exports LoReflection repair samples to DiffSynth `metadata.csv`.

## Boundaries

- Qwen-Image, Qwen2.5-VL, qwen-vl-finetune, DiffSynth-Studio, 3D-FRONT, and 3D-FUTURE are server-side dependencies.
- `third_party/` stores notes only unless you explicitly add wrappers.
- Model paths and dataset paths must remain placeholders locally.
