#!/usr/bin/env python3
"""Audit a proposed full-semantic Qwen target sample."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loreflection.semantic_registry import load_registry


def _load(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)


def _mask_for_colors(arr: np.ndarray, colors: set[tuple[int, int, int]]) -> np.ndarray:
    mask = np.zeros(arr.shape[:2], dtype=bool)
    for color in colors:
        mask |= np.all(arr == np.asarray(color, dtype=np.uint8), axis=-1)
    return mask


def audit(context_path: Path, furniture_path: Path, full_path: Path) -> dict:
    registry = load_registry()
    palette_colors = {cat.rgb for cat in registry.categories}
    furniture_colors = {registry.id_to_rgb[sid] for sid in registry.object_ids}
    architecture_colors = palette_colors - furniture_colors
    protected_names = {"wall", "door", "window", "clearance", "non_placeable"}
    protected_colors = {cat.rgb for cat in registry.categories if cat.name in protected_names}

    context = _load(context_path)
    furniture = _load(furniture_path)
    full = _load(full_path)
    if not (context.shape == furniture.shape == full.shape):
        raise ValueError("context, furniture, and full target must have the same resolution")

    context_arch = _mask_for_colors(context, architecture_colors)
    context_furn = _mask_for_colors(context, furniture_colors)
    furniture_furn = _mask_for_colors(furniture, furniture_colors)
    full_arch = _mask_for_colors(full, architecture_colors)
    full_furn = _mask_for_colors(full, furniture_colors)

    unknown_full = full.reshape(-1, 3)
    unknown_count = sum(1 for row in unknown_full if tuple(int(v) for v in row) not in palette_colors)
    non_furniture_region = ~furniture_furn
    architecture_preserved = np.all(context[non_furniture_region] == full[non_furniture_region], axis=-1)
    protected_mask = _mask_for_colors(context, protected_colors)
    forbidden_overwrite = int(np.logical_and(protected_mask, furniture_furn).sum())
    return {
        "context_image": str(context_path),
        "target_full_semantic": str(furniture_path),
        "target_full_semantic": str(full_path),
        "image_size": [int(context.shape[1]), int(context.shape[0])],
        "context_contains_architecture_categories": bool(context_arch.any()),
        "context_contains_furniture_categories": bool(context_furn.any()),
        "target_full_contains_architecture_categories": bool(full_arch.any()),
        "target_full_contains_furniture_categories": bool(full_furn.any()),
        "target_full_semantic_contains_furniture_categories": bool(furniture_furn.any()),
        "palette_unknown_pixel_count": int(unknown_count),
        "palette_valid": int(unknown_count) == 0,
        "architecture_preservation_rate_where_no_furniture": float(architecture_preserved.mean()),
        "forbidden_architecture_overwrite_pixels": forbidden_overwrite,
        "forbidden_architecture_overwrite_rate": forbidden_overwrite / max(1, int(furniture_furn.sum())),
        "status": "pass"
        if bool(context_arch.any())
        and not bool(context_furn.any())
        and bool(full_arch.any())
        and bool(full_furn.any())
        and int(unknown_count) == 0
        else "fail",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-image", type=Path, required=True)
    parser.add_argument("--target-full semantic", type=Path, required=True)
    parser.add_argument("--target-full-semantic", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = audit(args.context_image, args.target_full_semantic, args.target_full_semantic)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Full Semantic Target Contract Audit",
        "",
        f"- status: `{report['status']}`",
        f"- context_contains_architecture_categories: `{report['context_contains_architecture_categories']}`",
        f"- context_contains_furniture_categories: `{report['context_contains_furniture_categories']}`",
        f"- target_full_contains_architecture_categories: `{report['target_full_contains_architecture_categories']}`",
        f"- target_full_contains_furniture_categories: `{report['target_full_contains_furniture_categories']}`",
        f"- architecture_preservation_rate_where_no_furniture: `{report['architecture_preservation_rate_where_no_furniture']}`",
        f"- forbidden_architecture_overwrite_rate: `{report['forbidden_architecture_overwrite_rate']}`",
        f"- palette_valid: `{report['palette_valid']}`",
    ]
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
