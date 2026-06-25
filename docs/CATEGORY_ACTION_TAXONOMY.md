# Category Action Taxonomy

## Purpose

This is a converter schema cleanup for LoReflection. It is not a new paper
method contribution.

The cleanup separates:

- what the converter does with an object: `action`;
- what semantic group the object belongs to: `semantic_group`;
- why an object is skipped, when skipped: `skip_reason`.

## Why `keep_core` and `keep_lamp` Were Merged

`keep_core` and `keep_lamp` had identical processing behavior:

- both enter the furniture semantic layout;
- both enter Observed LoState `furniture_instances`;
- both are 2D semantic layout training targets;
- both are read back by the programmatic observer;
- both participate in furniture-level review.

Their difference is semantic grouping only. Core furniture uses
`semantic_group=core_furniture`; lamps use `semantic_group=lighting`.

## Why `skip_accessory` and `skip_unknown` Were Merged

`skip_accessory` and `skip_unknown` had identical processing behavior:

- neither enters the furniture semantic layout;
- neither enters Observed LoState;
- neither is a v1 training target.

Their difference is skip reason:

- accessory: `skip_reason=accessory_excluded_from_v1`;
- unknown: `skip_reason=unknown_or_unstable_mapping`.

## Canonical Actions

- `keep_furniture`: route to furniture semantic layout and Observed LoState.
- `keep_architecture_anchor`: route to Architecture JSON anchors and
  architecture condition image; never to Observed furniture.
- `keep_architecture_region`: route to Architecture JSON / condition metadata
  as a region; never to Observed furniture.
- `skip`: exclude from v1 semantic output and Observed LoState, but count in
  reports.

## Semantic Groups

- `core_furniture`
- `lighting`
- `architecture`
- `accessory`
- `unknown`

## Skip Reasons

- `accessory_excluded_from_v1`
- `unknown_or_unstable_mapping`

## Mapping Examples

```json
{
  "raw_category": "Dining Table",
  "loreflection_category": "table",
  "action": "keep_furniture",
  "semantic_group": "core_furniture"
}
```

```json
{
  "raw_category": "Pendant Lamp",
  "loreflection_category": "pendant_lamp",
  "action": "keep_furniture",
  "semantic_group": "lighting"
}
```

```json
{
  "raw_category": "Door",
  "loreflection_category": "door",
  "action": "keep_architecture_anchor",
  "semantic_group": "architecture"
}
```

```json
{
  "raw_category": "Curtain",
  "loreflection_category": "unknown",
  "action": "skip",
  "semantic_group": "accessory",
  "skip_reason": "accessory_excluded_from_v1"
}
```

## Converter Routing

```text
keep_furniture -> semantic layout + Observed LoState furniture_instances
keep_architecture_anchor -> Architecture JSON anchors + condition image
keep_architecture_region -> Architecture JSON / condition metadata
skip -> reports only
```

## Observed LoState Fields

Kept furniture entities write:

- `mapping_action=keep_furniture`
- `semantic_group=core_furniture | lighting`
- `category` remains the final LoReflection semantic category.

Lamp categories remain `pendant_lamp`, `ceiling_lamp`, and `lamp`; they are not
collapsed into a generic furniture class.

## Reports

Canonical fields:

- `furniture_kept_total`
- `furniture_kept_by_semantic_group`
- `architecture_kept_by_type`
- `skipped_total`
- `skipped_by_semantic_group`
- `skipped_by_reason`

Legacy compatibility fields may remain for one version:

- `core_furniture_kept`
- `lamp_kept`
- `accessory_skipped`
- `unknown_skipped`
- `core_unknown_count`
- `lamp_unknown_count`
- `core_missing_transform_count`
- `lamp_missing_transform_count`

These fields must be derived from `semantic_group`, not from legacy actions.

## Backward Compatibility

The converter keeps compatibility aliases:

```text
keep_core -> keep_furniture
keep_lamp -> keep_furniture
architecture_anchor -> keep_architecture_anchor
architecture_region -> keep_architecture_region
skip_accessory -> skip
skip_unknown -> skip
```

New config and new prototype outputs must not use legacy actions.

## Strict Validation Rules

`tools/audit_category_action_taxonomy.py` fails if:

- legacy action appears in the new mapping or prototype output;
- unknown action appears;
- semantic group is missing;
- skip reason is missing for skipped accessory/unknown items;
- `keep_furniture` lacks a LoReflection category;
- Observed LoState contains non-furniture actions;
- architecture entities appear in Observed LoState.
