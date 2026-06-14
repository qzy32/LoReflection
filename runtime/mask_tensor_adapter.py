#!/usr/bin/env python
"""Rasterize VLM mask_spec into a binary control_mask PNG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve(path_text: str, base_dir: Path | None) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() or base_dir is None else base_dir / path


def find_instance(observed: dict | None, instance_ref: str) -> dict:
    if not observed:
        raise ValueError("instance_ref masks require --observed-lostate.")
    for inst in observed.get("furniture_instances", []):
        if inst.get("instance_id") == instance_ref:
            return inst
    raise ValueError(f"instance_ref not found in observed LoState: {instance_ref}")


def validate_bbox(bbox: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    if len(bbox) != 4:
        raise ValueError(f"bbox_px must have four values, got {bbox}")
    x0, y0, x1, y1 = [int(round(v)) for v in bbox]
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"bbox_px must satisfy x1>x0 and y1>y0, got {bbox}")
    if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
        raise ValueError(f"bbox_px {bbox} is outside image_size_px [{width}, {height}]")
    return x0, y0, x1, y1


def rasterize_mask_spec(mask_spec: dict, observed_lostate: dict | None = None, observed_base_dir: Path | None = None) -> Image.Image:
    """Convert bbox, polygon, and instance_ref mask items into a binary PIL image."""
    width, height = mask_spec["image_size_px"]
    mask = Image.new("L", (width, height), 0)
    for item in mask_spec.get("items", []):
        item_type = item["type"]
        value = int(item.get("value", 255))
        layer = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(layer)
        if item_type == "bbox":
            x0, y0, x1, y1 = validate_bbox(item["bbox_px"], width, height)
            draw.rectangle([x0, y0, x1, y1], fill=value)
        elif item_type == "polygon":
            if len(item["polygon_px"]) < 3:
                raise ValueError("polygon_px masks require at least three points.")
            polygon = [(int(round(x)), int(round(y))) for x, y in item["polygon_px"]]
            for x, y in polygon:
                if x < 0 or y < 0 or x > width or y > height:
                    raise ValueError(f"polygon point [{x}, {y}] is outside image_size_px [{width}, {height}]")
            draw.polygon(polygon, fill=value)
        elif item_type == "instance_ref":
            inst = find_instance(observed_lostate, item["instance_ref"])
            if inst.get("mask_ref"):
                mask_path = resolve(inst["mask_ref"], observed_base_dir)
                if not mask_path.exists():
                    raise ValueError(f"mask_ref for instance {item['instance_ref']} does not exist: {mask_path}")
                inst_mask = Image.open(mask_path).convert("L").resize((width, height))
                layer = inst_mask.point(lambda p: value if p > 0 else 0)
            elif inst.get("bbox_px"):
                x0, y0, x1, y1 = validate_bbox(inst["bbox_px"], width, height)
                draw.rectangle([x0, y0, x1, y1], fill=value)
            else:
                raise ValueError(f"instance {item['instance_ref']} has neither mask_ref nor bbox_px.")
        else:
            raise ValueError(f"Unsupported mask item type: {item_type}")

        dilate_px = int(item.get("dilate_px", 0))
        if dilate_px > 0:
            layer = layer.filter(ImageFilter.MaxFilter(dilate_px * 2 + 1))
        mask = ImageChops.lighter(mask, layer)
    return mask.point(lambda p: 255 if p > 0 else 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mask-spec", required=True, type=Path, help="Input mask_spec JSON.")
    parser.add_argument("--observed-lostate", type=Path, help="Observed LoState JSON for instance_ref masks.")
    parser.add_argument("--control-image", type=Path, help="Optional control image; size must match mask_spec.image_size_px.")
    parser.add_argument("--output", required=True, type=Path, help="Output binary mask PNG.")
    args = parser.parse_args()

    mask_spec = load_json(args.mask_spec)
    if args.control_image:
        control_size = Image.open(args.control_image).size
        expected_size = tuple(mask_spec["image_size_px"])
        if control_size != expected_size:
            raise ValueError(f"control image size {control_size} does not match mask_spec.image_size_px {expected_size}")
    observed = load_json(args.observed_lostate) if args.observed_lostate else None
    observed_base = args.observed_lostate.parent if args.observed_lostate else None
    mask = rasterize_mask_spec(mask_spec, observed, observed_base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mask.save(args.output)
    print(f"Wrote binary control mask to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
