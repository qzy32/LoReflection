# SemLayoutDiff Adapter

SemLayoutDiff is connected to LoReflection as a third-party data and baseline source, not as the LoReflection main method.

Its roles are:

- Data preprocessing reference for 3D-FRONT / 3D-FUTURE.
- Source of architecture-conditioned room metadata and condition images.
- Source of fixed-palette semantic layouts.
- Architecture-conditioned semantic layout baseline for evaluation.

LoReflection still owns the reflective closed loop: Goal/Observed LoState, LoReview, RepairPlan, VLM mask planning, binary control masks, local inpainting execution, and acceptance.

## Reusable SemLayoutDiff Paths

The adapter expects, but does not require locally, these upstream files:

```text
SemLayoutDiff/preprocess/scripts/data_processor.py
SemLayoutDiff/preprocess/scripts/data_to_npy.py
SemLayoutDiff/preprocess/scripts/pickle_threed_front_dataset.py
SemLayoutDiff/preprocess/scripts/json_threed_future_dataset.py
SemLayoutDiff/render_dataset_improved_mat.py
SemLayoutDiff/scripts/train_sldn.py
SemLayoutDiff/scripts/sample_layout.py
```

Use `tools/inspect_semlayoutdiff_outputs.py` to check a local or server checkout without failing when the repo is absent.

## Output Mapping

```text
SemLayoutDiff / 3D-FRONT room metadata
-> LoReflection Architecture JSON

SemLayoutDiff semantic layout
-> LoReflection fixed-palette semantic layout

SemLayoutDiff sampled layout
-> LoReflection eval representation
```

The current local adapter implements the toy JSON version of the first two mappings. Real `.npy`, pickle, and upstream JSON field mappings are intentionally marked as TODO until inspected on the server.

## Server Paths

Configure these paths on the server:

```text
SEMLAYOUTDIFF_ROOT=/server/path/to/SemLayoutDiff
THREED_FRONT_ROOT=/server/path/to/3D-FRONT
THREED_FUTURE_ROOT=/server/path/to/3D-FUTURE
OUTPUT_ROOT=/server/path/to/loreflection_data
```

No local script downloads these assets.

## Local Toy Test

```bash
python tools/inspect_semlayoutdiff_outputs.py \
  --semlayoutdiff-root third_party/SemLayoutDiff \
  --sample-dir examples/toy_semlayoutdiff \
  --report experiments/val50/semlayoutdiff_inspect_report.json

python tools/convert_semlayoutdiff_to_loreflection.py \
  --input-root examples/toy_semlayoutdiff \
  --output-root outputs/semlayoutdiff_toy_loreflection \
  --palette configs/palette_v1.json \
  --mode toy

python tools/validate_all.py \
  --data-root outputs/semlayoutdiff_toy_loreflection \
  --strict
```

Expected final local status:

```text
SemLayoutDiff adapter toy conversion passed.
```

## Current TODO

- Map real SemLayoutDiff preprocessed `.npy` channel conventions to `configs/palette_v1.json`.
- Map real 3D-FRONT room metadata fields to `Architecture JSON` anchors and transforms.
- Decide whether SemLayoutDiff sampled outputs should be observed directly or first converted into LoReflection eval representation.
- Add server-side scripts that call upstream SemLayoutDiff training and sampling only after paths are manually configured.

