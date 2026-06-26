# Architecture Scale Contract

## Source Of Truth

The raw 3D-FRONT scene JSON is the source of truth for room architecture and real metric scale. Qwen output must never replace the original Architecture JSON or raw 3D-FRONT architecture record.

Qwen-Image Architecture In-Context Control is used only for furniture semantic image generation:

- Qwen does not generate architecture.
- Qwen generates furniture semantic image content only.
- `architecture_condition_image` is rendered from the raw 3D-FRONT-derived Architecture JSON.
- `target_semantic_layout_image` is rendered from the real furniture layout objects.
- Final inference still reads walls, room boundary, doors, windows, and architecture provenance from raw 3D-FRONT JSON / Architecture JSON.
- Qwen output is parsed only for furniture object masks.

## Furniture Inverse Transform

Furniture pixels from generated semantic images must be converted back to layout coordinates through the sample manifest and architecture transform information:

1. Parse only furniture connected components from the quantized Qwen semantic output.
2. Ignore floor, void, wall, door, window, clearance, and non-placeable architecture colors.
3. Use `sample_manifest`, `architecture.metric_transform`, or `render_transform` when present.
4. If explicit transform is missing in normalized_v1, recover an implicit inverse transform from `polygon_m` and `polygon_px` only as a baseline fallback.
5. Convert furniture masks back to `center_m`, `size_m`, and `footprint_m` before write-back.

## normalized_v1 Baseline

`normalized_v1` scales each room independently to a fixed image size. The pixel-to-world mapping can often be recovered mathematically from paired metric and pixel room polygons, but the condition image itself does not explicitly encode absolute room size differences across samples.

This means normalized_v1 is acceptable as a baseline for P0/P1-small route validation, but it should not be the default contract for formal P1/P2 training.

## metric_v2 Recommendation

`metric_v2` should use a fixed meter-per-pixel policy or a fixed metric canvas. In metric_v2:

- Different real room sizes remain visibly different in the condition image.
- Target and condition images use the same `metric_transform`.
- Qwen output is parsed back to metric layout using the same inverse transform.
- The raw 3D-FRONT Architecture JSON remains the architecture source of truth.
