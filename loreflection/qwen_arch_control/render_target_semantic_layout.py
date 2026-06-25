"""Render a palette-exact furniture-only semantic target image."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from loreflection.semantic_registry import SemanticRegistry, load_registry


def render_target_semantic_layout(
    layout: dict[str, Any],
    output_path: Path,
    image_size: int,
    registry: SemanticRegistry | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    palette = registry.name_to_rgb
    image = Image.new("RGB", (image_size, image_size), palette["void"])
    draw = ImageDraw.Draw(image)
    rendered = []
    for obj in layout.get("objects", []):
        category = str(obj["category"])
        if category not in palette or registry.name_to_id[category] not in registry.object_ids:
            raise ValueError(f"Target object is not a frozen furniture category: {category}")
        draw.rectangle(tuple(obj["bbox_px"]), fill=palette[category])
        rendered.append({"instance_id": obj["instance_id"], "category": category})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return {
        "image_size": [image_size, image_size],
        "palette_exact": True,
        "furniture_only": True,
        "rendered_objects": rendered,
    }
