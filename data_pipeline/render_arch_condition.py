#!/usr/bin/env python
"""Render a simple top-down architecture condition image from Architecture JSON using PIL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def make_transform(boundary: list[list[float]], width: int, height: int, pad: int):
    xs = [p[0] for p in boundary]
    ys = [p[1] for p in boundary]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    scale = min((width - 2 * pad) / max(max_x - min_x, 1e-6), (height - 2 * pad) / max(max_y - min_y, 1e-6))

    def tx(point: list[float]) -> tuple[int, int]:
        x, y = point
        px = pad + (x - min_x) * scale
        py = height - pad - (y - min_y) * scale
        return int(round(px)), int(round(py))

    return tx


def render(architecture: dict, output: Path, width: int, height: int) -> None:
    boundary = architecture["boundary"]["polygon_m"]
    tx = make_transform(boundary, width, height, pad=32)
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.polygon([tx(p) for p in boundary], fill="#F4F1E8", outline="#202020")
    draw.line([tx(p) for p in boundary + [boundary[0]]], fill="#202020", width=5)
    for anchor in architecture.get("anchors", []):
        kind = anchor.get("anchor_type")
        if "segment_m" in anchor:
            draw.line([tx(p) for p in anchor["segment_m"]], fill="#202020", width=8)
        elif "bbox_m" in anchor:
            x0, y0, x1, y1 = anchor["bbox_m"]
            color = "#D99058" if kind == "door" else "#5AB4E6"
            p0 = tx([x0, y0])
            p1 = tx([x1, y1])
            draw.rectangle([min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])], fill=color, outline="#202020")
        elif "polygon_m" in anchor:
            draw.polygon([tx(p) for p in anchor["polygon_m"]], outline="#999999")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--architecture", required=True, type=Path, help="Input Architecture JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG path.")
    parser.add_argument("--width", type=int, default=512, help="Image width.")
    parser.add_argument("--height", type=int, default=512, help="Image height.")
    args = parser.parse_args()
    render(load_json(args.architecture), args.output, args.width, args.height)
    print(f"Wrote architecture condition image to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
