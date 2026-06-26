from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_palette_contract(c2rgb_path: str | Path, id2c_path: str | Path | None = None) -> dict[str, Any]:
    """Load the frozen category-to-RGB contract without changing it."""
    c2rgb_file = Path(c2rgb_path)
    if not c2rgb_file.exists():
        raise FileNotFoundError(c2rgb_file)
    raw = json.loads(c2rgb_file.read_text(encoding="utf-8"))
    colors = raw.get("colors", raw)
    c2rgb: dict[str, list[int]] = {}
    for name, value in colors.items():
        if isinstance(value, str):
            value = value.strip().lstrip("#")
            rgb = [int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)]
        else:
            rgb = [int(v) for v in value]
        c2rgb[str(name)] = rgb

    id2c = None
    if id2c_path:
        id2c_file = Path(id2c_path)
        if id2c_file.exists():
            id2c = json.loads(id2c_file.read_text(encoding="utf-8"))

    return {
        "schema_version": "palette-contract-v1",
        "c2rgb_path": c2rgb_file.as_posix(),
        "id2c_path": Path(id2c_path).as_posix() if id2c_path else None,
        "c2rgb": c2rgb,
        "id2c": id2c,
    }


def get_active_palette_entries(required_counts: dict[str, Any], c2rgb: dict[str, list[int]]) -> dict[str, list[int]]:
    active: dict[str, list[int]] = {}
    for category, count in sorted(required_counts.items()):
        try:
            enabled = int(count) > 0
        except (TypeError, ValueError):
            enabled = bool(count)
        if enabled and category in c2rgb:
            active[category] = [int(v) for v in c2rgb[category]]
    return active


def validate_active_palette_entries(active_categories: list[str], c2rgb: dict[str, list[int]]) -> dict[str, Any]:
    missing = [category for category in active_categories if category not in c2rgb]
    invalid_rgb = []
    for category in active_categories:
        rgb = c2rgb.get(category)
        if rgb is None:
            continue
        if len(rgb) != 3 or any(int(v) < 0 or int(v) > 255 for v in rgb):
            invalid_rgb.append(category)
    return {
        "valid": not missing and not invalid_rgb,
        "missing_categories": missing,
        "invalid_rgb_categories": invalid_rgb,
    }


def build_palette_control_prompt(active_categories: list[str], include_rgb: bool = False) -> str:
    if include_rgb:
        category_text = ", ".join(active_categories)
    else:
        category_text = ", ".join(active_categories)
    if not category_text:
        category_text = "the active furniture categories"
    return (
        "Palette_Control. Generate a fixed-palette semantic layout only. "
        "Use the frozen category-to-color semantic palette. "
        "Draw each active furniture category with its assigned palette color only. "
        "Do not generate realistic texture, material, lighting, shadow, gradient, anti-aliasing, or unknown colors. "
        f"Active semantic categories: {category_text}."
    )
