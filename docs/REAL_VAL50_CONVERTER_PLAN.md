# Real Val50 Converter Prototype Plan

## Scope

This step builds only a bounded 5-scene prototype before any val50 expansion.
The data source is the `EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle`.
It must not be described as a freshly downloaded official raw archive.

## What This Prototype Does

- Samples a small number of 3D-FRONT scene JSON files.
- Builds a 3D-FUTURE `model_info.json` category index.
- Generates minimal LoReflection Architecture JSON.
- Generates fixed-palette top-down semantic layout PNG previews.
- Generates Observed LoState JSON with source JID and uncertainty fields.
- Writes a manifest, mapping report, warning report, and contact sheet.

## What This Prototype Does Not Do

- It does not download data.
- It does not download models.
- It does not train Qwen-VL, Qwen-Image, DiffSynth, or EditRoom.
- It does not run Blender.
- It does not run Qwen-VL, Qwen-Image, or DiffSynth inference.
- It does not full-convert 3D-FRONT.
- It does not claim perfect geometry.

## Geometry Policy

Boundary, furniture size, orientation, and top-down placement are read only
when the fields are available and recognizable. If exact fields are not
available, the converter must write explicit warnings such as
`boundary_source = bbox_fallback` or `size from category prior fallback`.

Fallback geometry is acceptable for this prototype because the goal is to
exercise the interface and preview audit path, not to finalize the dataset.

## Repaired Converter Policy

After reference pipeline mining, the converter uses a stricter 3D-FRONT parser:

- Category mapping is three-layer:
  `3D-FUTURE raw category -> SemLayoutDiff/reference category -> LoReflection palette category`.
- The LoReflection palette is not replaced.
- Each Observed LoState entity keeps `raw_category`, `reference_category`, and
  `loreflection_category`.
- Transform extraction uses `scene.room[*].children` first. The link order is:
  `child.ref == furniture.uid`, `child.uid == furniture.uid`,
  `child.instanceid == furniture.uid`, `child.jid == furniture.jid`,
  then `child.ref == furniture.jid`.
- Each entity records `transform_source` and `size_source`.
- Boundary extraction tries floor-like mesh, then room bbox, then furniture bbox
  fallback.
- If all bounded scenes remain `bbox_fallback`, the converter should not scale
  to 50.

The repaired output is written to:

```text
/wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1_repaired
```

The repaired run also writes:

```text
reports/before_after_comparison_report.json
```

## SemLayoutDiff-Aligned R2 Policy

R2 aligns the converter with the SemLayoutDiff label policy:

- `door`, `window`, `wall`, and `floor` are not furniture entities.
- Door/window-like objects become Architecture JSON anchors and are rendered in
  `architecture_condition_v1/*.architecture_condition.png`.
- `curtain` is `skip_accessory` in v1 and is not drawn in the furniture semantic
  map.
- `Pendant Lamp`, `Ceiling Lamp`, and generic `lamp` are furniture semantic
  outputs and remain in Observed LoState.
- Each kept entity stores `raw_category`, `reference_category`,
  `loreflection_category`, `mapping_action`, `transform_source`, `size_source`,
  and `is_lamp`.
- Non-core skipped objects are counted in reports instead of being mixed into
  global unknown furniture quality metrics.

R2 output is written to:

```text
/wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1_semantics_aligned
```

## Palette Alias Fix R4

R3.5 verified that `sofa -> chair` and `table -> desk` are unsafe aliases.
3D-FUTURE raw categories preserve sofa-like and table-like objects as
independent semantic categories, so the converter must keep them as native
LoReflection palette classes before visual audit.

R4 policy:

- `Three-Seat / Multi-seat Sofa`, `Loveseat Sofa`, `L-shaped Sofa`, and `Sofa`
  map to `sofa`.
- `Dining Table`, `Coffee Table`, `Corner/Side Table`, and `Table` map to
  `table`.
- `Pendant Lamp`, `Ceiling Lamp`, and generic lamp-like objects remain lamp
  furniture outputs.
- `door` and `window` remain architecture anchors and must not enter Observed
  LoState furniture entities.
- Alias audit hard-fails if sofa-to-chair or table-to-desk mappings appear in
  mapping rules or generated entities.

R4 output is written to:

```text
/wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1_palette_fixed
```

## Architecture Condition and Boundary-Derived Wall Policy

R5 clarifies how wall/boundary should be represented before scaling beyond the
bounded 5-scene prototype:

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

R5 output is written to:

```text
/wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1_arch_validated
```

## Category Action Taxonomy

R6 separates converter behavior from semantic grouping:

- `action` describes processing behavior;
- `semantic_group` describes semantic grouping;
- lamps are independent training categories but share `keep_furniture` with
  other furniture;
- door/window are `keep_architecture_anchor`;
- floor/clearance/room mask style regions are `keep_architecture_region`;
- accessory and unknown items share `skip`, with different `semantic_group` and
  `skip_reason`;
- old actions are deprecated compatibility aliases only.

Canonical actions:

```text
keep_furniture
keep_architecture_anchor
keep_architecture_region
skip
```

R6 output is written to:

```text
/wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1_action_refactored
```

## Required Manual Audit

After conversion, inspect:

- `preview/contact_sheet.png`
- `preview/per_scene/*.png`
- `reports/conversion_report.json`
- `reports/field_warnings.json`
- `category_mapping_v1/jid_mapping_report.json`

The prototype can scale to 50 scenes only after the contact sheet and warning
summary look reasonable.

## Server Command

```bash
python3 tools/build_real_val50_prototype.py \
  --env-file server_configs/paths.local.env \
  --output-root /wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1 \
  --num-scenes 5 \
  --seed 42 \
  --image-size 512 \
  --strict

python3 tools/inspect_val50_prototype_outputs.py \
  --package-root /wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1 \
  --report /wuqingyaoa800/qiuziyan/loreflection_outputs/val50_prototype_v1/reports/audit_report.json \
  --strict
```
