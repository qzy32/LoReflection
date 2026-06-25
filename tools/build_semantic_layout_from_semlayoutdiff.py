#!/usr/bin/env python
"""Convert toy SemLayoutDiff semantic objects to fixed-palette semantic PNG.

Status: toy compatibility adapter.

This output-level adapter is retained for Step 2.2 interface regression only.
The native real-data preprocessing pipeline reads raw 3D-FRONT / 3D-FUTURE and
does not use this script.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def hex_to_rgb(text: str) -> tuple[int, int, int]:
    text = text.lstrip("#")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))


def draw_toy_json(input_path: Path, palette_path: Path, output_path: Path, default_size: int = 1024) -> dict:
    payload = load_json(input_path)
    palette = load_json(palette_path)["colors"]
    width, height = payload.get("image_size_px", [default_size, default_size])
    image = Image.new("RGB", (width, height), palette.get("floor", "#F4F1E8"))
    draw = ImageDraw.Draw(image)
    draw.rectangle([24, 24, width - 24, height - 24], outline=palette.get("wall", "#202020"), width=8)
    warnings: list[str] = []
    for obj in payload.get("objects", []):
        category = obj["category"]
        color = palette.get(category)
        if not color:
            warnings.append(f"Unknown category {category}; skipped.")
            continue
        bbox = obj.get("bbox_px")
        if not bbox:
            warnings.append(f"Object {obj.get('object_id', category)} has no bbox_px; skipped.")
            continue
        draw.rectangle([int(v) for v in bbox], fill=color)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return {"converted": True, "warnings": warnings}


def convert_png_palette_map(input_path: Path, palette_path: Path, output_path: Path) -> dict:
    palette = load_json(palette_path)["colors"]
    known = {hex_to_rgb(value): hex_to_rgb(value) for value in palette.values()}
    background = hex_to_rgb(palette.get("background", "#FFFFFF"))
    image = Image.open(input_path).convert("RGB")
    output = Image.new("RGB", image.size, background)
    src = image.load()
    dst = output.load()
    unknown_count = 0
    for y in range(image.height):
        for x in range(image.width):
            rgb = src[x, y]
            if rgb in known:
                dst[x, y] = known[rgb]
            else:
                unknown_count += 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(output_path)
    warnings = []
    if unknown_count:
        warnings.append(f"{unknown_count} pixels did not match configs/palette_v1.json and were mapped to background.")
    return {"converted": True, "warnings": warnings}


def npy_placeholder(input_path: Path, output_path: Path) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1024, 1024), "#FFFFFF").save(output_path)
    report_path = output_path.with_suffix(".npy_placeholder_report.json")
    report = {
        "schema_version": "semlayoutdiff-npy-placeholder-report-v1",
        "input": str(input_path),
        "output": str(output_path),
        "todo": "Map real SemLayoutDiff npy channel/category conventions to configs/palette_v1.json on the server.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"converted": False, "warnings": [f"npy_placeholder mode wrote TODO report to {report_path}"]}


def convert_semantic_layout(input_path: Path, palette_path: Path, output_path: Path, mode: str) -> dict:
    if output_path.suffix.lower() != ".png":
        raise ValueError("--output must be a PNG path.")
    if mode == "toy_json":
        return draw_toy_json(input_path, palette_path, output_path)
    if mode == "png_palette_map":
        return convert_png_palette_map(input_path, palette_path, output_path)
    if mode == "npy_placeholder":
        return npy_placeholder(input_path, output_path)
    raise ValueError(f"Unsupported mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="semantic_objects.json, PNG palette map, or npy placeholder path.")
    parser.add_argument("--palette", type=Path, default=Path("configs/palette_v1.json"), help="LoReflection palette JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output fixed-palette PNG.")
    parser.add_argument("--mode", required=True, choices=["toy_json", "png_palette_map", "npy_placeholder"], help="Input conversion mode.")
    args = parser.parse_args()

    result = convert_semantic_layout(args.input, args.palette, args.output, args.mode)
    print(json.dumps({"output": str(args.output), **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
