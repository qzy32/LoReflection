# Reference Pipeline Mining

## Purpose

Step 3.2B produced a structurally valid 5-scene prototype, but the warnings
show that converter quality is not ready for val50 scaling. Before repairing
the converter, LoReflection mines existing 3D-FRONT preprocessing pipelines as
reference pipelines.

The goal is to understand how mature pipelines handle:

- 3D-FUTURE category normalization into semantic classes.
- 3D-FRONT furniture links from object metadata to scene transform nodes.
- Room, floor, boundary, and room-mask extraction.
- Semantic layout / boxes / npy artifact generation.

## Reference Sources

- SemLayoutDiff preprocessing and sampling code.
- EditRoom dataset and preprocessing code.
- ATISS / DiffuScene-style preprocessing patterns when visible through the
  local reference code.
- The bounded 5-scene LoReflection prototype package.

These sources are used as engineering references. LoReflection should adapt
the ideas to its own schemas, palette, and provenance policy. Do not copy a
baseline implementation blindly.

## What Can Be Borrowed

- Category vocabulary candidates and normalization strategy.
- Furniture metadata to transform-node linking rules.
- Room-mask or floor-plan extraction logic.
- Box and semantic map field conventions.
- Diagnostics for missing JID, missing transform, and fallback geometry.

## What Cannot Be Treated As Raw Source

- Processed SemLayoutDiff PNGs are not raw 3D-FRONT geometry.
- EditRoom preprocessed artifacts should not be described as a freshly
  downloaded official archive.
- Unknown category should not become a real semantic class.
- Bounding-box fallback should not be the default path for val50.

## Next Repair Direction

Use the mining report to repair `tools/build_real_val50_prototype.py` in a
separate step:

1. Replace ad-hoc category normalization with a documented mapping derived from
   3D-FUTURE `model_info.json` and SemLayoutDiff/ATISS-style class evidence.
2. Parse nested 3D-FRONT scene child transforms before using grid fallback.
3. Recover room/floor boundary candidates from mesh or room-mask references.
4. Add regression counters so unknown category, transform fallback, and
   bbox-fallback boundary rates are visible before scaling to 50 scenes.
