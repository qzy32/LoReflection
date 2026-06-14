#!/usr/bin/env python
"""Programmatic fixed-palette semantic layout observer."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

from PIL import Image


def hex_to_rgb(text: str) -> tuple[int, int, int]:
    text = text.lstrip("#")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def connected_components(pixels: list[list[bool]]) -> list[list[tuple[int, int]]]:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    comps = []
    for y in range(height):
        for x in range(width):
            if seen[y][x] or not pixels[y][x]:
                continue
            q = deque([(x, y)])
            seen[y][x] = True
            comp = []
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
                    if 0 <= nx < width and 0 <= ny < height and not seen[ny][nx] and pixels[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            comps.append(comp)
    return comps


def observe(image_path: Path, architecture: dict, palette: dict, output_dir: Path, min_area_px: int = 16) -> dict:
    """Convert a fixed-palette image into an Observed LoState with bbox and mask_ref fields."""
    image = Image.open(image_path).convert("RGB")
    rgb = image.load()
    width, height = image.size
    color_by_category = {name: hex_to_rgb(value) for name, value in palette["colors"].items()}
    ignore = {"background", "floor", "wall", "door", "window"}
    instances = []
    masks_dir = output_dir / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    for category, color in color_by_category.items():
        if category in ignore:
            continue
        bitmap = [[rgb[x, y] == color for x in range(width)] for y in range(height)]
        for idx, comp in enumerate(connected_components(bitmap)):
            if len(comp) < min_area_px:
                continue
            xs = [p[0] for p in comp]
            ys = [p[1] for p in comp]
            instance_id = f"{category}_{idx + 1}"
            mask = Image.new("L", (width, height), 0)
            mask_pixels = mask.load()
            for x, y in comp:
                mask_pixels[x, y] = 255
            mask_ref = masks_dir / f"{instance_id}.png"
            mask.save(mask_ref)
            instances.append(
                {
                    "instance_id": instance_id,
                    "category": category,
                    "bbox_px": [min(xs), min(ys), max(xs) + 1, max(ys) + 1],
                    "area_px": len(comp),
                    "mask_ref": str(mask_ref.relative_to(output_dir)),
                }
            )
    return {
        "schema_version": "observed-lostate-v1",
        "state_role": "observed",
        "metadata": {"task_id": image_path.stem, "repair_round": 0, "source_image": str(image_path)},
        "architecture_ref": {"architecture_id": architecture["architecture_id"]},
        "semantic_registry_ref": {
            "palette_id": palette["palette_id"],
            "category_set": "indoor_furniture_categories_v1",
            "relation_set": "layout_relations_v1",
        },
        "room_type": architecture.get("room_type", "room"),
        "furniture_instances": instances,
        "measured_relations": [],
        "hard_constraint_evidence": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path, help="Fixed-palette semantic layout image.")
    parser.add_argument("--architecture", required=True, type=Path, help="Architecture JSON.")
    parser.add_argument("--palette", type=Path, default=Path("configs/palette_v1.json"), help="Palette JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Observed LoState JSON.")
    parser.add_argument("--min-area-px", type=int, default=16, help="Minimum connected component area.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    observed = observe(args.image, load_json(args.architecture), load_json(args.palette), args.output.parent, args.min_area_px)
    args.output.write_text(json.dumps(observed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote observed LoState to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

