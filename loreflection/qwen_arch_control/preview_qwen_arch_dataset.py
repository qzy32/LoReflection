"""Generate HTML and contact-sheet previews for a P0 package."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def build_preview(dataset_root: Path, max_contact_samples: int = 12) -> dict[str, Any]:
    preview_root = dataset_root / "previews"
    preview_root.mkdir(parents=True, exist_ok=True)
    with (dataset_root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    cards = []
    for row in rows:
        goal = json.loads((dataset_root / row["goal_lostate"]).read_text(encoding="utf-8"))
        manifest_path = dataset_root / "meta" / f"{row['sample_id']}_sample_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        required = [slot["category"] for slot in goal["furniture_slots"] if slot["required"]]
        cards.append(
            "<section><h2>{sid}</h2><div class='images'>"
            "<figure><img src='../{cond}'><figcaption>architecture_condition_image</figcaption></figure>"
            "<figure><img src='../{target}'><figcaption>target_semantic_layout_image</figcaption></figure>"
            "</div><p><b>Room:</b> {room}</p><p><b>Required:</b> {required}</p>"
            "<p><b>Prompt:</b> {prompt}</p><p><b>Warnings:</b> {warnings}</p></section>".format(
                sid=html.escape(row["sample_id"]),
                cond=html.escape(row["context_image"]),
                target=html.escape(row["image"]),
                room=html.escape(goal["room_type"]),
                required=html.escape(", ".join(required)),
                prompt=html.escape(row["prompt"]),
                warnings=html.escape(", ".join(manifest.get("warnings", [])) or "none"),
            )
        )
    page = """<!doctype html><meta charset="utf-8"><title>Qwen Arch Control P0</title>
<style>body{font-family:Arial,sans-serif;max-width:1200px;margin:24px auto;color:#20242a}
section{border-bottom:1px solid #ddd;padding:18px 0}.images{display:flex;gap:18px}
figure{margin:0}img{width:360px;image-rendering:pixelated;border:1px solid #aaa}
figcaption{font-size:13px;margin-top:4px}p{line-height:1.45}</style>
<h1>Qwen-Image Architecture In-Context P0 Preview</h1>
<p>Condition is architecture-only. Target is furniture-only. This package is a deterministic procedural contract set, not a real 3D-FRONT benchmark split.</p>
""" + "\n".join(cards)
    (preview_root / "index.html").write_text(page, encoding="utf-8")

    selected = rows[:max_contact_samples]
    tile = 256
    label_height = 28
    sheet = Image.new("RGB", (tile * 2, (tile + label_height) * len(selected)), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for idx, row in enumerate(selected):
        y = idx * (tile + label_height)
        condition = Image.open(dataset_root / row["context_image"]).convert("RGB").resize((tile, tile))
        target = Image.open(dataset_root / row["image"]).convert("RGB").resize((tile, tile))
        sheet.paste(condition, (0, y))
        sheet.paste(target, (tile, y))
        draw.text((6, y + tile + 7), f"{row['sample_id']} | condition", fill=(0, 0, 0), font=font)
        draw.text((tile + 6, y + tile + 7), "target", fill=(0, 0, 0), font=font)
    sheet.save(preview_root / "contact_sheet.png")
    return {
        "num_html_samples": len(rows),
        "num_contact_samples": len(selected),
        "index_html": str(preview_root / "index.html"),
        "contact_sheet": str(preview_root / "contact_sheet.png"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--max-contact-samples", type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(build_preview(args.dataset_root, args.max_contact_samples), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
