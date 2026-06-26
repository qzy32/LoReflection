#!/usr/bin/env python3
"""Build one full-semantic target review sample from an existing Qwen record."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loreflection.qwen_arch_control.render_full_semantic_target import compose_full_semantic_target


def _copy(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _side_by_side(paths: list[Path], labels: list[str], output: Path) -> None:
    images = [Image.open(path).convert("RGB") for path in paths]
    width = sum(img.width for img in images)
    label_h = 28
    height = max(img.height for img in images) + label_h
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    x = 0
    for image, label in zip(images, labels):
        canvas.paste(image, (x, label_h))
        draw.text((x + 4, 6), label, fill=(0, 0, 0))
        x += image.width
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def _legend(target_path: Path, palette_entries_path: Path, output: Path) -> None:
    image = Image.open(target_path).convert("RGB")
    entries = json.loads(palette_entries_path.read_text(encoding="utf-8"))
    row_h = 28
    legend_w = 260
    canvas = Image.new("RGB", (image.width + legend_w, max(image.height, row_h * max(1, len(entries)))), "white")
    canvas.paste(image, (0, 0))
    draw = ImageDraw.Draw(canvas)
    x0 = image.width + 12
    y = 8
    for name, rgb in entries.items():
        color = tuple(int(v) for v in rgb)
        draw.rectangle((x0, y, x0 + 20, y + 20), fill=color)
        draw.text((x0 + 28, y + 3), name, fill=(0, 0, 0))
        y += row_h
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-review-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    src = args.source_review_dir
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    context = src / "context_image.png"
    furniture = src / "target_semantic.png"
    full = out / "target_full_semantic.png"
    full_report = compose_full_semantic_target(
        context_image_path=context,
        furniture_target_path=furniture,
        output_path=full,
    )

    _copy(context, out / "context_image.png")
    _copy(furniture, out / "target_furniture_only.png")
    for name in ["goal_lostate.json", "prompt_package.json", "palette_entries.json", "metric_transform.json"]:
        _copy(src / name, out / name)
    _side_by_side(
        [out / "context_image.png", out / "target_furniture_only.png", full],
        ["context: architecture-only", "target: furniture-only", "target_full: architecture+furniture"],
        out / "side_by_side_context_furniture_full.png",
    )
    _legend(full, out / "palette_entries.json", out / "target_full_semantic_with_palette_legend.png")

    record = json.loads((src / "training_record.json").read_text(encoding="utf-8"))
    payload = {
        **record,
        "target_furniture_only": "target_furniture_only.png",
        "target_full_semantic": "target_full_semantic.png",
        "qwen_full_semantic_metadata_image_should_point_to": "target_full_semantic.png",
        "full_semantic_report": full_report,
        "metadata_field_design": {
            "image": "target_full_semantic",
            "target_full_semantic": "target_full_semantic",
            "target_furniture_only": "target_furniture_only",
            "context_image": "architecture-only condition",
        },
    }
    (out / "training_record_full_semantic.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md = [
        "# Full Semantic Qwen Training Record Review",
        "",
        f"- sample_id: `{record.get('sample_id')}`",
        f"- room_type: `{record.get('room_type', 'unknown')}`",
        f"- metadata_source: `{record.get('metadata_source')}`",
        "- context_image: architecture-only semantic condition.",
        "- target_furniture_only: current LoReflection furniture-layer supervision.",
        "- target_full_semantic: proposed architecture + furniture supervision.",
        "- Qwen full-semantic metadata `image` should point to `target_full_semantic.png`.",
        "",
        "![context](context_image.png)",
        "",
        "![furniture only](target_furniture_only.png)",
        "",
        "![full semantic](target_full_semantic.png)",
        "",
        "![side by side](side_by_side_context_furniture_full.png)",
        "",
        "![legend](target_full_semantic_with_palette_legend.png)",
        "",
        "## Prompt",
        "",
        record.get("prompt", ""),
        "",
        "## Compiled Prompt",
        "",
        record.get("compiled_prompt", ""),
        "",
        "## Goal LoState Summary",
        "",
        f"- required_counts: `{json.dumps(record.get('required_counts', {}), ensure_ascii=False)}`",
        f"- pairwise_constraints: `{json.dumps(record.get('pairwise_constraints', []), ensure_ascii=False)}`",
        f"- global_constraints: `{json.dumps(record.get('global_constraints', []), ensure_ascii=False)}`",
        "",
        "## Palette Entries",
        "",
        "```json",
        json.dumps(record.get("active_palette_entries", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Metric Transform",
        "",
        "```json",
        json.dumps(record.get("metric_transform", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Full Semantic Contract Report",
        "",
        "```json",
        json.dumps(full_report, ensure_ascii=False, indent=2),
        "```",
    ]
    (out / "training_record_full_semantic.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
