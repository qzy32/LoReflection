"""Render a palette-exact architecture-only condition image."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from loreflection.semantic_registry import SemanticRegistry, load_registry


def render_architecture_condition(
    architecture: dict[str, Any],
    output_path: Path,
    image_size: int,
    registry: SemanticRegistry | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    palette = registry.name_to_rgb
    image = Image.new("RGB", (image_size, image_size), palette["void"])
    draw = ImageDraw.Draw(image)
    boundary = architecture["boundary"]["polygon_px"]
    draw.polygon([tuple(point) for point in boundary], fill=palette["floor"])

    anchor_counts = {"door": 0, "window": 0, "clearance": 0, "non_placeable": 0}
    for anchor in architecture.get("anchors", []):
        anchor_type = str(anchor.get("anchor_type", ""))
        box = anchor.get("bbox_px")
        polygon = anchor.get("polygon_px")
        if anchor_type in {"door", "window"} and box:
            draw.rectangle(tuple(box), fill=palette[anchor_type])
            anchor_counts[anchor_type] += 1
        elif anchor_type in {"clearance", "non_placeable"} and polygon:
            # The frozen registry has no separate clearance class. Retain it as
            # architecture floor support without introducing an unknown color.
            draw.polygon([tuple(point) for point in polygon], fill=palette["floor"])
            anchor_counts[anchor_type] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return {
        "image_size": [image_size, image_size],
        "palette_exact": True,
        "architecture_only": True,
        "anchor_counts": anchor_counts,
        "wall_representation": "floor-to-void boundary edge; frozen registry has no wall category",
    }
