#!/usr/bin/env python3
"""Build a visual review sheet for P0 Architecture In-Context inference."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _load_eval(eval_path: Path) -> dict:
    return json.loads(eval_path.read_text(encoding="utf-8")) if eval_path.exists() else {}


def _sample_ids(infer_dir: Path) -> list[str]:
    return [p.name[: -len("_raw.png")] for p in sorted(infer_dir.glob("*_raw.png"))]


def _agreement(a: Path, b: Path) -> float | None:
    if not a.exists() or not b.exists():
        return None
    arr_a = np.array(Image.open(a).convert("RGB"))
    arr_b = np.array(Image.open(b).convert("RGB"))
    if arr_a.shape != arr_b.shape:
        return None
    return float((arr_a == arr_b).all(axis=2).mean())


def _thumb(path: Path, size: int = 160) -> Image.Image:
    if not path.exists():
        im = Image.new("RGB", (size, size), (240, 240, 240))
        draw = ImageDraw.Draw(im)
        draw.text((10, 70), "missing", fill=(0, 0, 0))
        return im
    return Image.open(path).convert("RGB").resize((size, size), Image.Resampling.NEAREST)


def build_review(output_root: Path, dataset_base: Path, metadata_path: Path) -> dict:
    infer_dir = output_root / "infer"
    quant_dir = output_root / "quantized"
    eval_dir = output_root / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    rows = {row["sample_id"]: row for row in csv.DictReader(metadata_path.open("r", encoding="utf-8", newline=""))}
    ids = _sample_ids(infer_dir)
    row_h = 210
    col_w = 180
    text_w = 520
    width = col_w * 4 + text_w
    height = max(row_h, row_h * max(1, len(ids)))
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for r, sid in enumerate(ids):
        y = r * row_h
        row = rows.get(sid, {})
        condition = infer_dir / f"{sid}_condition.png"
        target = infer_dir / f"{sid}_target.png"
        raw = infer_dir / f"{sid}_raw.png"
        quant = quant_dir / f"{sid}_quantized.png"
        for c, (label, path) in enumerate(
            [("condition", condition), ("target", target), ("raw", raw), ("quantized", quant)]
        ):
            x = c * col_w
            sheet.paste(_thumb(path), (x, y + 22))
            draw.text((x + 4, y + 4), label, fill=(0, 0, 0))
        agreement = _agreement(quant, target)
        prompt_path = infer_dir / f"{sid}_prompt.txt"
        prompt = prompt_path.read_text(encoding="utf-8", errors="ignore") if prompt_path.exists() else row.get("prompt", "")
        text = [
            f"sample_id: {sid}",
            f"pixel agreement: {agreement if agreement is not None else 'n/a'}",
            "prompt:",
            prompt[:520],
        ]
        draw.multiline_text((col_w * 4 + 10, y + 8), "\n".join(text), fill=(0, 0, 0), spacing=4)
    png_path = eval_dir / "p0_infer_review_sheet.png"
    sheet.save(png_path)
    html_rows = []
    for sid in ids:
        prompt_path = infer_dir / f"{sid}_prompt.txt"
        prompt = prompt_path.read_text(encoding="utf-8", errors="ignore") if prompt_path.exists() else ""
        agreement = _agreement(quant_dir / f"{sid}_quantized.png", infer_dir / f"{sid}_target.png")
        html_rows.append(
            "<tr>"
            f"<td>{html.escape(sid)}</td>"
            f"<td><img src='../infer/{sid}_condition.png'></td>"
            f"<td><img src='../infer/{sid}_target.png'></td>"
            f"<td><img src='../infer/{sid}_raw.png'></td>"
            f"<td><img src='../quantized/{sid}_quantized.png'></td>"
            f"<td>{agreement if agreement is not None else 'n/a'}</td>"
            f"<td><pre>{html.escape(prompt)}</pre></td>"
            "</tr>"
        )
    html_path = eval_dir / "p0_infer_review.html"
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>img{width:160px;height:160px;image-rendering:pixelated}td{vertical-align:top;border:1px solid #ddd;padding:6px}pre{white-space:pre-wrap;max-width:520px}</style>"
        "</head><body><h1>P0 Inference Review</h1><table>"
        "<tr><th>sample</th><th>condition</th><th>target</th><th>raw</th><th>quantized</th><th>pixel agreement</th><th>prompt</th></tr>"
        + "\n".join(html_rows)
        + "</table></body></html>",
        encoding="utf-8",
    )
    report = {"num_samples": len(ids), "png": str(png_path), "html": str(html_path), "eval": _load_eval(eval_dir / "p0_sanity_eval_report.json")}
    (eval_dir / "p0_infer_review_sheet_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dataset-base", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    build_review(args.output_root, args.dataset_base, args.metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
