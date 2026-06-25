# Palette Alias And 3D-FRONT Parser Audit

## Purpose

Step 3.2B-R2 aligned the prototype with SemLayoutDiff label policy, but two
items must be audited before any scale-up:

- Palette aliases such as sofa-to-chair, table-to-desk, and cabinet-to-wardrobe
  need explicit counts and severity.
- Wall and architecture-condition generation need deeper SemLayoutDiff parser
  evidence.

## Palette Alias Policy

Aliases are acceptable for a 5-scene prototype only when they are explicitly
reported. The audit groups aliases by:

- raw category
- reference category
- LoReflection category
- mapping action
- count
- alias reason
- severity

Safe aliases are small semantic merges that preserve the current palette.
Review aliases may deserve dedicated palette categories before val50. Risky
aliases should block scale-up until decided.

## SemLayoutDiff Parser Inspection

The parser inspection focuses on:

- raw 3D-FRONT fields: top-level furniture, scene room children, mesh, model
  info
- object geometry: center, size, rotation/orientation, scale, bbox
- architecture condition: floor, wall, door, window, opening, room mask
- semantic outputs: label map, instance annotations, boxes

SemLayoutDiff processed outputs can validate policy and expected artifacts, but
they must not be treated as raw geometry.

## Excluded External Project Parser

The user-provided `parse_json_floorplan.py` belongs to an unrelated Chinese
PlanJSON project. It is not authoritative for LoReflection's current
3D-FRONT / 3D-FUTURE / SemLayoutDiff taxonomy, palette, mapping, registry, or
training provenance.

The active taxonomy must be derived strictly from the SemLayoutDiff official
source checkout and metadata. Any category names that happen to overlap with
the Chinese PlanJSON script are coincidence, not evidence.

## Before Scale50

- Review all alias rows and decide whether to expand palette categories.
- Decide whether wall must be explicitly rasterized beyond boundary outline.
- Keep door/window as architecture anchors.
- Keep lamp classes as furniture semantic outputs.
- Keep curtain/decor skipped unless the target palette expands.
