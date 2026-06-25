#!/usr/bin/env python3
"""Audit that architecture_condition_image does not contain furniture colors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loreflection.semantic_registry import load_registry


ALLOWED_ARCHITECTURE_NAMES = {
    "void",
    "floor",
    "wall",
    "door",
    "window",
    "room_mask",
    "clearance",
    "non_placeable",
    "opening",
    "background",
    "outline",
}
FORBIDDEN_FURNITURE_KEYWORDS = {
    "bed",
    "sofa",
    "table",
    "chair",
    "wardrobe",
    "desk",
    "cabinet",
    "stand",
    "shelf",
    "stool",
    "dresser",
    "tv",
}


def _load_palette(path: Path) -> dict[str, tuple[int, int, int]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    colors = payload.get("colors", payload)
    out = {}
    for name, color in colors.items():
        if isinstance(color, str):
            value = color.strip().lstrip("#")
            rgb = (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
        else:
            rgb = tuple(int(v) for v in color)
        out[str(name)] = rgb
    return out


def _forbidden_colors(registry_root: Path) -> dict[tuple[int, int, int], str]:
    registry = load_registry(registry_root)
    forbidden = {}
    for category in registry.categories:
        name = category.name
        if category.role == "object" or any(word in name for word in FORBIDDEN_FURNITURE_KEYWORDS):
            forbidden[category.rgb] = name
    palette = _load_palette(registry_root / "palette_frozen.json")
    for name, rgb in palette.items():
        if name not in ALLOWED_ARCHITECTURE_NAMES and any(word in name for word in FORBIDDEN_FURNITURE_KEYWORDS):
            forbidden[rgb] = name
    return forbidden


def audit_image(image_path: Path, registry_root: Path) -> dict[str, Any]:
    forbidden = _forbidden_colors(registry_root)
    image = Image.open(image_path).convert("RGB")
    colors = image.getcolors(maxcolors=image.width * image.height) or []
    violations = []
    for count, rgb in colors:
        if rgb in forbidden:
            violations.append({"rgb": list(rgb), "category": forbidden[rgb], "pixel_count": count})
    return {
        "image_path": str(image_path),
        "registry_root": str(registry_root),
        "unique_color_count": len(colors),
        "furniture_color_violations": violations,
        "status": "pass" if not violations else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--registry-root", type=Path, default=Path("artifacts/semantic_registry_v2"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.image is None:
        parser.print_help()
        return 0
    report = audit_image(args.image, args.registry_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
