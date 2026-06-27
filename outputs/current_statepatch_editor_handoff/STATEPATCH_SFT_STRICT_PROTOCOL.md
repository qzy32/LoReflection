# StatePatch SFT Strict Protocol

This document defines the strict StatePatch subset for VLM SFT and inference.

The JSON schema is intentionally wider than the training subset. Programmatic tools may accept multiple update modes, but VLM SFT and inference must not mix all available degrees of freedom. The current training and inference contract is the strict subset below.

## Overall Rule

The VLM returns one StatePatch JSON only.

The VLM does not output bbox, footprint, complete layout JSON, complete scene JSON, source_json_path, engine uid, RepairPlan, mask_spec, control_mask, I_bad, I_target, or blockwise ControlNet fields.

The executor resolves observed references and writes executable layout_json / scene_json.

## ADD / Insert

ADD only uses `new_instance`.

Allowed fields:

- `new_instance.update_mode = append`
- `new_instance.category`
- `new_instance.asset_id`, optional
- `new_instance.size_hint`, optional
- `new_instance.placement_hint`, optional

Forbidden:

- `bbox`
- `bbox_m`
- `bbox_px`
- `footprint`
- `center_m`
- `source_json_path`
- direct complete `layout_json` / `scene_json`

Explanation:

The VLM only states what category to insert, with optional asset, size hint, and placement hint. Concrete center, orientation, bbox, and polygon are decided by the executor and local solver.

## REMOVE / Delete

REMOVE only needs:

- `target.target_ref`
- `target.expected_category`
- `reason`
- `constraints_to_satisfy`
- `protected_refs`

Forbidden:

- `bbox`
- `bbox_m`
- `bbox_px`
- `footprint`
- `state_field_updates`

Explanation:

The removed object is resolved by `target_ref`. The VLM does not need and must not output bbox coordinates for the removed object.

## TRANSLATE / Move

TRANSLATE only allows:

- `center_m.update_mode = relative_delta`
- `center_m.delta_m = [dx_m, dz_m]`

Forbidden:

- `center_m.update_mode = absolute`
- `center_m.value_m`
- `bbox`
- `bbox_m`
- `bbox_px`
- `footprint`

Explanation:

The VLM only outputs the relative movement. It does not output the final absolute center and does not output bbox. The executor computes `new_center = old_center + delta_m` and recomputes bbox / polygon.

## ROTATE

ROTATE only allows:

- `orientation_deg.update_mode = relative_delta`
- `orientation_deg.delta_deg`

Forbidden:

- `orientation_deg.update_mode = absolute`
- `orientation_deg.value_deg`

Explanation:

The VLM outputs a relative rotation such as `+90` or `-45`. The executor computes the new orientation and recomputes footprint / bbox.

## SCALE

SCALE only allows:

- `size_m.update_mode = relative_scale`
- `size_m.scale_xy = [scale_x, scale_z]`

Forbidden:

- `size_m.update_mode = absolute`
- `size_m.value_m`
- `bbox`

Explanation:

The VLM outputs scale factors, not the new absolute size and not bbox. The executor computes `new_size = old_size * scale_xy`.

## REPLACE

REPLACE allows:

- `category.update_mode = absolute`
- `category.value`
- `asset_id.update_mode = absolute`, optional
- `asset_id.value`, optional
- `size_m.relative_scale.scale_xy`, optional

Forbidden:

- `bbox`
- `bbox_m`
- `bbox_px`
- `footprint`
- complete `layout_json`
- complete `scene_json`

Explanation:

The VLM states which observed object should be replaced and what category or asset it should become. The executor should preserve center / orientation where possible, estimate or solve the new size, recompute geometry, and send the candidate to verifier.

## Executor

Executor is deterministic code, not the VLM.

Executor is responsible for:

1. schema validate
2. resolve `target.target_ref` against Observed LoState
3. copy source `layout_json` / `scene_json` into candidate
4. apply `state_field_updates`
5. recompute center / size / orientation / footprint / bbox / polygon
6. write candidate `layout_json` / `scene_json`
7. call verifier
8. accept / reject / rollback

## Verifier

Verifier is a deterministic geometry / rule checking module.

Verifier checks:

- `inside_room`
- `avoid_overlap`
- `door_clearance_free`
- `window_clearance_free`
- `required_count_match`
- `protected_refs` unchanged
- category consistency
- relation constraints if required

## Local Solver

Local solver only performs small local search / snap / clamp near the patch.

It is not a global layout generator.

It does not replace VLM decision-making.

It only adjusts the VLM patch into a geometrically feasible local edit.

## Recommended Training Subset Summary

| Action | VLM outputs | VLM must not output |
|---|---|---|
| ADD | `new_instance.category` / `asset_id` / `size_hint` / `placement_hint` | bbox, center_m, footprint |
| REMOVE | `target_ref` | bbox, state_field_updates |
| TRANSLATE | `center_m.relative_delta.delta_m` | absolute value_m, bbox |
| ROTATE | `orientation_deg.relative_delta.delta_deg` | absolute value_deg |
| SCALE | `size_m.relative_scale.scale_xy` | absolute value_m, bbox |
| REPLACE | category / asset_id / optional relative scale | bbox, full JSON |
