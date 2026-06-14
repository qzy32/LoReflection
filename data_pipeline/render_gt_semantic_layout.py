#!/usr/bin/env python
"""Render a toy fixed-palette semantic layout image for local smoke tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render(goal_lostate: dict, palette: dict, output: Path, width: int, height: int) -> None:
    colors = palette["colors"]
    image = Image.new("RGB", (width, height), colors["floor"])
    draw = ImageDraw.Draw(image)
    draw.rectangle([24, 24, width - 24, height - 24], outline=colors["wall"], width=6)
    placements = {
        "bed": [70, 160, 250, 330],
        "nightstand": [260, 220, 315, 280],
        "wardrobe": [345, 70, 465, 170],
        "desk": [330, 315, 460, 390],
        "chair": [360, 395, 425, 455],
    }
    for slot in goal_lostate.get("furniture_slots", []):
        category = slot.get("category")
        if category in placements:
            draw.rectangle(placements[category], fill=colors.get(category, "#888888"))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-lostate", required=True, type=Path, help="Goal LoState JSON.")
    parser.add_argument("--palette", type=Path, default=Path("configs/palette_v1.json"), help="Palette JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output semantic layout PNG.")
    parser.add_argument("--width", type=int, default=512, help="Image width.")
    parser.add_argument("--height", type=int, default=512, help="Image height.")
    args = parser.parse_args()
    render(load_json(args.goal_lostate), load_json(args.palette), args.output, args.width, args.height)
    print(f"Wrote toy semantic layout to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

