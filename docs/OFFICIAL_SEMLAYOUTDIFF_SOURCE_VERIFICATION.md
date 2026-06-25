# Official SemLayoutDiff Source Verification

## Purpose

This note records Step 3.2B-R3.5: verifying SemLayoutDiff source evidence before changing the LoReflection palette or category aliases.

The goal is narrow:

- verify official SemLayoutDiff preprocessing evidence;
- separate official SemLayoutDiff evidence from local or external parser references;
- decide whether current aliases such as `sofa -> chair` and `Dining Table -> desk` are safe.

No data is downloaded, no model is downloaded, no training is started, and no full 3D-FRONT conversion is run in this step.

## Correction

The uploaded `parse_json_floorplan.py` is not official SemLayoutDiff source. It belongs to another related project and can only be used as an external parser policy reference.

It may inform category or rendering policy at a high level, for example:

- keeping `pendant_lamp` and `ceiling_lamp` as semantic objects;
- treating `door` and `window` as building or architecture canvas classes;
- filtering `curtain` and decorative objects as non-core or void classes.

It must not be cited as official SemLayoutDiff implementation evidence, and its field-reading logic must not be copied into the 3D-FRONT converter because it parses a different plan JSON format.

## Official Source Scope

The official SemLayoutDiff source scope for this audit is:

```text
preprocess/scripts/data_processor.py
preprocess/scripts/data_to_npy.py
preprocess/scripts/front3d.py
preprocess/scripts/json_threed_future_dataset.py
preprocess/scripts/pickle_threed_front_dataset.py
preprocess/scripts/pickle_threed_future_dataset.py
preprocess/scripts/utils.py
preprocess/scripts/utils/
preprocess/metadata/*.json
preprocess/metadata/*.csv
configs/*.yaml
configs/**/*.yaml
```

The official GitHub reference is:

```text
https://github.com/3dlg-hcvc/SemLayoutDiff/tree/main/preprocess/scripts
```

## Expected Hard Evidence

The official `pickle_threed_front_dataset.py` is the parser entry for 3D-FRONT scenes. It calls `parse_threed_front_scenes_from_dataset` from `threed_front.datasets.parse_utils`, with paths to:

- the 3D-FRONT scene JSON directory;
- the 3D-FUTURE model directory;
- `model_info.json`.

This means SemLayoutDiff relies on the `threed_front` parsing stack for raw scene parsing. LoReflection should reuse the parser policy and the parsed object structure, but should not blindly copy unrelated local parser files as official SemLayoutDiff logic.

## Palette Alias Implication

The current LoReflection aliases must be checked before visual audit:

- `sofa -> chair` is unsafe if raw 3D-FUTURE / SemLayoutDiff evidence contains sofa-like categories.
- `Dining Table -> desk` is unsafe if raw 3D-FUTURE / SemLayoutDiff evidence contains table-like categories.
- Lamp categories should remain furniture semantic outputs when supported by raw category evidence.
- Door and window should remain architecture anchors or architecture-condition labels, not furniture entities.

## Recommendation

Proceed to palette fix only after the generated report confirms the alias conflict. The expected fix is:

- add or restore independent `sofa` and `table` LoReflection palette categories;
- map sofa-like raw/reference classes to `sofa`;
- map table-like raw/reference classes to `table`;
- keep `pendant_lamp`, `ceiling_lamp`, and generic `lamp` as furniture semantic outputs;
- keep `door` and `window` out of Observed LoState furniture entities and preserve them in Architecture JSON anchors / architecture condition images.

Do not claim:

- the uploaded parser is official SemLayoutDiff source;
- the local EditRoom-provided data bundle is freshly downloaded official raw 3D-FRONT / 3D-FUTURE;
- SemLayoutDiff directly implements every child/ref parsing detail if the official evidence shows the entry delegates to `threed_front.datasets.parse_utils`.

## Architecture Condition and Boundary-Derived Wall Policy

LoReflection follows the SemLayoutDiff-style split between architecture
condition and furniture semantic output:

- wall is not a furniture entity;
- wall is not generated as an Observed LoState furniture instance;
- wall is an immutable architecture reference;
- raw explicit wall anchors are preferred but not required;
- if raw wall anchors are unavailable, boundary-derived wall segments are used;
- floor/room mask and boundary contour are part of the architecture condition image;
- door/window are architecture anchors and must not enter furniture entities;
- `wall_anchor_count=0` is acceptable only when `derived_wall_segment_count>0`
  and the boundary contour exists;
- `against_wall_reference_source` must not be `missing` before scale50.
