"""Compose full semantic Qwen targets from architecture and furniture layers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from loreflection.semantic_registry import SemanticRegistry, load_registry


def _rgb_sets(registry: SemanticRegistry) -> tuple[dict[tuple[int, int, int], str], set[tuple[int, int, int]]]:
    rgb_to_name = {cat.rgb: cat.name for cat in registry.categories}
    furniture_colors = {registry.id_to_rgb[sid] for sid in registry.object_ids}
    return rgb_to_name, furniture_colors


def compose_full_semantic_target(
    *,
    context_image_path: Path,
    furniture_target_path: Path,
    output_path: Path,
    registry: SemanticRegistry | None = None,
) -> dict[str, Any]:
    """Overlay furniture semantic pixels onto an architecture condition image.

    The output is intended for Qwen full-semantic target ablations:
    architecture pixels come from ``context_image`` and furniture pixels come
    from the existing full semantic target. This function does not repair
    geometry. If furniture overlaps non-floor architecture, it records the
    overwrite in the report instead of silently fixing it.
    """

    registry = registry or load_registry()
    palette = registry.name_to_rgb
    rgb_to_name, furniture_colors = _rgb_sets(registry)
    context = np.asarray(Image.open(context_image_path).convert("RGB"), dtype=np.uint8)
    furniture = np.asarray(Image.open(furniture_target_path).convert("RGB"), dtype=np.uint8)
    if context.shape != furniture.shape:
        raise ValueError(f"Image shape mismatch: {context.shape} vs {furniture.shape}")

    furniture_mask = np.zeros(context.shape[:2], dtype=bool)
    for color in furniture_colors:
        furniture_mask |= np.all(furniture == np.asarray(color, dtype=np.uint8), axis=-1)

    protected_names = {"wall", "door", "window", "clearance", "non_placeable"}
    protected_colors = {palette[name] for name in protected_names if name in palette}
    protected_mask = np.zeros(context.shape[:2], dtype=bool)
    for color in protected_colors:
        protected_mask |= np.all(context == np.asarray(color, dtype=np.uint8), axis=-1)

    out = context.copy()
    out[furniture_mask] = furniture[furniture_mask]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, mode="RGB").save(output_path)

    flat_out = out.reshape(-1, 3)
    unique_colors = {tuple(int(v) for v in row) for row in flat_out}
    unknown_colors = sorted(color for color in unique_colors if color not in rgb_to_name)
    architecture_colors_in_target = {
        name
        for color, name in rgb_to_name.items()
        if name not in {registry.id_to_name[sid] for sid in registry.object_ids}
        and np.all(out == np.asarray(color, dtype=np.uint8), axis=-1).any()
    }
    furniture_colors_in_target = {
        name
        for color, name in rgb_to_name.items()
        if color in furniture_colors and np.all(out == np.asarray(color, dtype=np.uint8), axis=-1).any()
    }

    overwritten_protected = int(np.logical_and(furniture_mask, protected_mask).sum())
    return {
        "output_path": str(output_path),
        "image_size": [int(context.shape[1]), int(context.shape[0])],
        "palette_exact": not unknown_colors,
        "unknown_colors": unknown_colors,
        "target_contains_architecture_categories": sorted(architecture_colors_in_target),
        "target_contains_furniture_categories": sorted(furniture_colors_in_target),
        "furniture_pixel_count": int(furniture_mask.sum()),
        "protected_architecture_overwrite_pixels": overwritten_protected,
        "forbidden_architecture_overwrite_rate": overwritten_protected / max(1, int(furniture_mask.sum())),
    }
