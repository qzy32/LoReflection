"""Metric-v2 architecture-only condition renderer.

Architecture comes from raw 3D-FRONT-derived Architecture JSON. Qwen does not
produce architecture; this renderer produces only the conditioning image.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from loreflection.qwen_arch_control.metric_transform import world_to_pixel
from loreflection.semantic_registry import SemanticRegistry, load_registry


def _object_colors(registry: SemanticRegistry) -> set[tuple[int, int, int]]:
    return {registry.id_to_rgb[sid] for sid in registry.object_ids}


def _normalize_box(box: list[Any] | tuple[Any, ...], image_size: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = [int(round(float(v))) for v in box]
    left, right = sorted((x0, x1))
    top, bottom = sorted((y0, y1))
    return (
        max(0, min(image_size - 1, left)),
        max(0, min(image_size - 1, top)),
        max(0, min(image_size - 1, right)),
        max(0, min(image_size - 1, bottom)),
    )


def render_architecture_condition_metric(
    architecture: dict[str, Any],
    output_path: Path,
    image_size: int,
    registry: SemanticRegistry | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    palette = registry.name_to_rgb
    transform = architecture.get("metric_transform")
    if not isinstance(transform, dict):
        raise ValueError("metric_v2 architecture rendering requires architecture.metric_transform")
    image = Image.new("RGB", (image_size, image_size), palette["void"])
    draw = ImageDraw.Draw(image)
    boundary_m = architecture["boundary"].get("polygon_m") or []
    if not boundary_m:
        raise ValueError("metric_v2 architecture rendering requires boundary.polygon_m")
    boundary_px = [world_to_pixel((float(p[0]), float(p[1])), transform) for p in boundary_m]
    draw.polygon(boundary_px, fill=palette["floor"])

    anchor_counts = {"door": 0, "window": 0, "clearance": 0, "non_placeable": 0}
    for anchor in architecture.get("anchors", []):
        atype = str(anchor.get("anchor_type", ""))
        if atype not in anchor_counts:
            continue
        polygon_m = anchor.get("polygon_m")
        box_m = anchor.get("bbox_m")
        box_px = anchor.get("bbox_px")
        polygon_px = anchor.get("polygon_px")
        if polygon_m:
            px = [world_to_pixel((float(p[0]), float(p[1])), transform) for p in polygon_m]
            draw.polygon(px, fill=palette[atype] if atype in {"door", "window"} else palette["floor"])
            anchor_counts[atype] += 1
        elif box_m:
            x0, z0, x1, z1 = [float(v) for v in box_m]
            p0 = world_to_pixel((x0, z0), transform)
            p1 = world_to_pixel((x1, z1), transform)
            draw.rectangle(_normalize_box([p0[0], p0[1], p1[0], p1[1]], image_size), fill=palette[atype] if atype in {"door", "window"} else palette["floor"])
            anchor_counts[atype] += 1
        elif box_px:
            draw.rectangle(_normalize_box(box_px, image_size), fill=palette[atype] if atype in {"door", "window"} else palette["floor"])
            anchor_counts[atype] += 1
        elif polygon_px:
            draw.polygon([tuple(point) for point in polygon_px], fill=palette[atype] if atype in {"door", "window"} else palette["floor"])
            anchor_counts[atype] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    arr = np.array(image.convert("RGB"))
    object_colors = _object_colors(registry)
    flat = arr.reshape(-1, 3)
    contains_furniture = any(tuple(int(v) for v in pixel) in object_colors for pixel in flat)
    floor = np.array(palette["floor"], dtype=np.uint8)
    floor_pixel_area = int((arr == floor).all(axis=2).sum())
    return {
        "renderer": "render_architecture_condition_metric_v2",
        "image_size": [image_size, image_size],
        "palette_exact": True,
        "architecture_only": True,
        "scale_policy": transform.get("scale_policy"),
        "canvas_extent_m": transform.get("canvas_extent_m"),
        "pixels_per_meter": transform.get("pixels_per_meter"),
        "boundary_source": architecture.get("boundary", {}).get("source") or architecture.get("boundary", {}).get("boundary_source"),
        "floor_pixel_area": floor_pixel_area,
        "condition_contains_furniture": bool(contains_furniture),
        "anchor_counts": anchor_counts,
    }
