# EditRoom Adapter

EditRoom is connected to LoReflection only as an editing data and baseline source. It is not the LoReflection main method.

## Role In LoReflection

EditRoom is used for:

- Editing pair source.
- Perturbation reference.
- Editing baseline.
- Planner SFT data construction.
- DiffSynth / ControlNet repair sample construction.

LoReflection still owns the reflective loop: Goal/Observed LoState, LoReview, RepairPlan, VLM mask planning, binary control masks, inpainting repair execution, re-observation, and acceptance.

## Recommended Reusable Paths

```text
EditRoom/tools/generate_perturbations.py
EditRoom/tools/editroomperturb.py
EditRoom/tools/generate_prompt.py
EditRoom/src/train_edit.py
EditRoom/configs/bedroom_sg2sc_diffusion.yaml
EditRoom/configs/bedroom_sg_diffusion.yaml
```

The local adapter only checks for these files. It does not run EditRoom training or inference.

## edit_type Mapping

```text
INSERT -> issue_type=entity_missing or edit_insert, action_type=INSERT, mask_spec=bbox/polygon
DELETE -> issue_type=entity_extra or edit_delete, action_type=DELETE, mask_spec=instance_ref
REPLACE -> issue_type=category_mismatch or edit_replace, action_type=REPLACE, mask_spec=instance_ref/bbox
MOVE -> issue_type=relation_issue or edit_move, action_type=MOVE, mask_spec=old_new_union
```

## Output Mapping

```text
EditRoom before layout -> LoReflection control_image / Observed LoState source
EditRoom after layout -> LoReflection target_image
EditRoom edit instruction -> correction_prompt
EditRoom changed region -> mask_spec / control_mask
EditRoom pair -> Planner SFT + DiffSynth repair sample
```

The local toy adapter renders simple fixed-palette PNGs from bbox-based layout JSON. Real EditRoom field names and graph formats must be inspected on the server before adding real-data modes.

## Server Path Placeholders

```text
EDITROOM_ROOT=/server/path/to/EditRoom
EDITROOM_DATA_ROOT=/server/path/to/editroom_data
OUTPUT_ROOT=/server/path/to/loreflection_data
```

No local script downloads these assets or starts training.

## Local Toy Test

```bash
python tools/inspect_editroom_outputs.py \
  --editroom-root third_party/EditRoom \
  --sample-dir examples/toy_editroom \
  --report experiments/val50/editroom_inspect_report.json

python tools/convert_editroom_to_loreflection.py \
  --input-root examples/toy_editroom \
  --output-root outputs/editroom_toy_loreflection \
  --mode toy

python tools/validate_all.py \
  --data-root outputs/editroom_toy_loreflection \
  --strict
```

Expected final local status:

```text
EditRoom adapter toy conversion passed.
```

## Current TODO

- Confirm real EditRoom pair manifests and scene graph field names.
- Map real EditRoom perturbation outputs to LoReflection `RepairPlan` and `mask_spec`.
- Map real EditRoom rendered or generated layouts into fixed-palette semantic PNGs.
- Decide whether EditRoom baseline outputs should be evaluated through Observed LoState or direct eval representation conversion.
- Add server-only scripts for real EditRoom processing after paths are manually configured.

