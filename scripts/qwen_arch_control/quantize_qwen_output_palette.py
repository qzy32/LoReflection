#!/usr/bin/env python3
"""Nearest-neighbor quantize Qwen outputs to the frozen semantic palette."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from loreflection.semantic_registry import load_registry


def _palette() -> np.ndarray:
    registry = load_registry()
    return np.array([cat.rgb for cat in registry.categories], dtype=np.float32)


def _sample_id(path: Path) -> str:
    name = path.name
    return name[:-8] if name.endswith("_raw.png") else path.stem


def quantize_outputs(input_dir: Path, output_dir: Path, report_path: Path) -> dict[str, object]:
    palette = _palette()
    exact = {tuple(int(v) for v in row) for row in palette.astype(np.uint8)}
    output_dir.mkdir(parents=True, exist_ok=True)
    reports: list[dict[str, object]] = []
    raw_paths = sorted(input_dir.glob("*_raw.png"))
    total_pixels = 0
    unknown_before = 0
    unknown_after = 0
    distance_sum = 0.0
    max_distance = 0.0

    for path in raw_paths:
        arr = np.array(Image.open(path).convert("RGB"), dtype=np.float32)
        flat = arr.reshape(-1, 3)
        before_unknown = sum(tuple(int(v) for v in pixel) not in exact for pixel in flat)
        distances = ((flat[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2)
        nearest_idx = distances.argmin(axis=1)
        nearest_dist = np.sqrt(distances[np.arange(len(flat)), nearest_idx])
        if len(nearest_dist):
            max_distance = max(max_distance, float(nearest_dist.max()))
        quant = palette[nearest_idx].reshape(arr.shape).astype(np.uint8)
        sid = _sample_id(path)
        out_path = output_dir / f"{sid}_quantized.png"
        Image.fromarray(quant).save(out_path)
        after_flat = quant.reshape(-1, 3)
        after_unknown = sum(tuple(int(v) for v in pixel) not in exact for pixel in after_flat)
        total_pixels += len(flat)
        unknown_before += before_unknown
        unknown_after += after_unknown
        distance_sum += float(nearest_dist.sum())
        reports.append(
            {
                "sample_id": sid,
                "input": str(path),
                "output": str(out_path),
                "unknown_color_rate_before_quantization": before_unknown / max(1, len(flat)),
                "unknown_color_rate_after_quantization": after_unknown / max(1, len(flat)),
                "mean_palette_distance": float(nearest_dist.mean()),
                "max_palette_distance": float(nearest_dist.max()) if len(nearest_dist) else 0.0,
            }
        )

    report = {
        "num_images": len(raw_paths),
        "unknown_color_rate_before_quantization": unknown_before / max(1, total_pixels),
        "unknown_color_rate_after_quantization": unknown_after / max(1, total_pixels),
        "mean_palette_distance": distance_sum / max(1, total_pixels),
        "max_palette_distance": max_distance,
        "samples": reports,
        "status": "pass" if raw_paths else "no_inputs",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    quantize_outputs(args.input_dir, args.output_dir, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
