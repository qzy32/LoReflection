#!/usr/bin/env python3
"""Audit whether Qwen target images contain architecture or furniture colors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loreflection.semantic_registry import load_registry


def _count_categories(image_path: Path) -> dict[str, int]:
    registry = load_registry()
    arr = np.asarray(Image.open(image_path).convert("RGB"), dtype=np.uint8)
    counts: dict[str, int] = {}
    for category in registry.categories:
        color = np.asarray(category.rgb, dtype=np.uint8)
        count = int(np.all(arr == color, axis=-1).sum())
        if count:
            counts[category.name] = count
    unknown = arr.shape[0] * arr.shape[1] - sum(counts.values())
    if unknown:
        counts["__unknown_rgb__"] = int(unknown)
    return counts


def _split_counts(counts: dict[str, int]) -> dict[str, Any]:
    registry = load_registry()
    object_names = {registry.id_to_name[sid] for sid in registry.object_ids}
    structural_names = {
        "floor",
        "wall",
        "door",
        "window",
        "clearance",
        "non_placeable",
        "room_mask",
    }
    furniture = {name: count for name, count in counts.items() if name in object_names}
    architecture = {
        name: count
        for name, count in counts.items()
        if name not in object_names and not name.startswith("__")
    }
    structural = {name: count for name, count in architecture.items() if name in structural_names}
    return {
        "architecture_pixel_count": int(sum(architecture.values())),
        "structural_architecture_pixel_count": int(sum(structural.values())),
        "void_background_pixel_count": int(architecture.get("void", 0)),
        "furniture_pixel_count": int(sum(furniture.values())),
        "architecture_categories": architecture,
        "structural_architecture_categories": structural,
        "furniture_categories": furniture,
        "unknown_pixel_count": int(counts.get("__unknown_rgb__", 0)),
    }


def audit_pair(context_image: Path, target_image: Path) -> dict[str, Any]:
    context_counts = _split_counts(_count_categories(context_image))
    target_counts = _split_counts(_count_categories(target_image))
    return {
        "context_image": str(context_image),
        "target_image": str(target_image),
        "context": context_counts,
        "target": target_counts,
        "context_contains_furniture": context_counts["furniture_pixel_count"] > 0,
        "target_contains_architecture": target_counts["structural_architecture_pixel_count"] > 0,
        "target_contains_furniture": target_counts["furniture_pixel_count"] > 0,
        "target_interpretation": (
            "full_semantic_architecture_plus_furniture"
            if target_counts["structural_architecture_pixel_count"] > 0 and target_counts["furniture_pixel_count"] > 0
            else "full_semantic"
            if target_counts["furniture_pixel_count"] > 0
            else "not_verified"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-image", type=Path, required=True)
    parser.add_argument("--target-image", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = audit_pair(args.context_image, args.target_image)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# LoReflection Current Target Audit",
        "",
        f"- context_image: `{report['context_image']}`",
        f"- target_image: `{report['target_image']}`",
        f"- context_contains_furniture: `{report['context_contains_furniture']}`",
        f"- target_contains_architecture: `{report['target_contains_architecture']}`",
        f"- target_contains_furniture: `{report['target_contains_furniture']}`",
        f"- target_interpretation: `{report['target_interpretation']}`",
        "",
        "## Context category pixels",
        "```json",
        json.dumps(report["context"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Target category pixels",
        "```json",
        json.dumps(report["target"], ensure_ascii=False, indent=2),
        "```",
    ]
    args.output_md.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
