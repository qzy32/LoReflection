"""Render a palette-exact full semantic semantic target image.

Qwen target images contain full semantic. Architecture and scale remain sourced
from raw 3D-FRONT-derived Architecture JSON and its metric transform.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from loreflection.qwen_arch_control.metric_transform import world_to_pixel
from loreflection.semantic_registry import SemanticRegistry, load_registry


def _oriented_rect(center: list[float], size: list[float], orientation_deg: float) -> list[list[float]]:
    cx, cz = float(center[0]), float(center[1])
    w, d = float(size[0]), float(size[1])
    theta = math.radians(float(orientation_deg))
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    return [[cx + dx * cos_t - dz * sin_t, cz + dx * sin_t + dz * cos_t] for dx, dz in corners]


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


def render_target_semantic_layout(
    layout: dict[str, Any],
    output_path: Path,
    image_size: int,
    registry: SemanticRegistry | None = None,
    architecture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    palette = registry.name_to_rgb
    transform = None
    if architecture and isinstance(architecture.get("metric_transform"), dict):
        transform = architecture["metric_transform"]
    elif isinstance(layout.get("metric_transform"), dict):
        transform = layout["metric_transform"]
    image = Image.new("RGB", (image_size, image_size), palette["void"])
    draw = ImageDraw.Draw(image)
    rendered = []
    fallback_count = 0
    for obj in layout.get("objects", []):
        category = str(obj["category"])
        if category not in palette or registry.name_to_id[category] not in registry.object_ids:
            raise ValueError(f"Target object is not a frozen furniture category: {category}")
        render_source = "bbox_px_fallback"
        if transform and obj.get("footprint_m"):
            polygon = [world_to_pixel((float(p[0]), float(p[1])), transform) for p in obj["footprint_m"]]
            draw.polygon(polygon, fill=palette[category])
            render_source = "footprint_m_oriented"
        elif transform and obj.get("center_m") and obj.get("size_m"):
            footprint = _oriented_rect(obj["center_m"], obj["size_m"], float(obj.get("orientation_deg", 0.0)))
            polygon = [world_to_pixel((float(p[0]), float(p[1])), transform) for p in footprint]
            draw.polygon(polygon, fill=palette[category])
            render_source = "center_size_orientation"
        else:
            draw.rectangle(_normalize_box(obj["bbox_px"], image_size), fill=palette[category])
            fallback_count += 1
        rendered.append({"instance_id": obj["instance_id"], "category": category, "render_source": render_source})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    object_count = len(layout.get("objects", []))
    return {
        "image_size": [image_size, image_size],
        "palette_exact": True,
        "full_semantic": True,
        "uses_metric_transform": bool(transform),
        "target_bbox_fallback_rate": fallback_count / max(1, object_count),
        "rendered_objects": rendered,
    }
