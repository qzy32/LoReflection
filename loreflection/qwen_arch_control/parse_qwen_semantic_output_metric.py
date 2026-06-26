#!/usr/bin/env python3
"""Parse quantized Qwen semantic furniture output into candidate layout JSON."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from loreflection.qwen_arch_control.metric_transform import pixel_to_world
from loreflection.semantic_registry import load_registry


def _bbox(points: list[list[float]]) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _pixel_to_world(x: float, y: float, arch: dict[str, Any]) -> tuple[float | None, float | None, str]:
    transform = arch.get("metric_transform")
    if isinstance(transform, dict):
        wx, wy = pixel_to_world((x, y), transform)
        return wx, wy, "metric_transform"
    boundary = arch.get("boundary", {}) if isinstance(arch.get("boundary"), dict) else {}
    poly_m = boundary.get("polygon_m") or []
    poly_px = boundary.get("polygon_px") or []
    bm = _bbox(poly_m)
    bp = _bbox(poly_px)
    if bm is None or bp is None:
        return None, None, "unavailable"
    px_w = max(1e-9, bp[2] - bp[0])
    px_h = max(1e-9, bp[3] - bp[1])
    mx = bm[0] + ((x - bp[0]) / px_w) * (bm[2] - bm[0])
    my = bm[1] + ((y - bp[1]) / px_h) * (bm[3] - bm[1])
    return float(mx), float(my), "implicit_polygon_bbox_fallback"


def _component_bfs(mask: np.ndarray) -> list[tuple[int, int, int, int, int, float, float]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
    for yy in range(h):
        for xx in range(w):
            if not mask[yy, xx] or seen[yy, xx]:
                continue
            q = deque([(xx, yy)])
            seen[yy, xx] = True
            xs = []
            ys = []
            while q:
                x, y = q.popleft()
                xs.append(x); ys.append(y)
                for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((nx, ny))
            comps.append((min(xs), min(ys), max(xs)+1, max(ys)+1, len(xs), float(sum(xs)/len(xs)), float(sum(ys)/len(ys))))
    return comps


def parse_output(image_path: Path, architecture_path: Path, manifest_path: Path | None, min_area: int = 4) -> dict[str, Any]:
    registry = load_registry()
    rgb_to_cat = {tuple(rgb): name for name, rgb in registry.name_to_rgb.items()}
    furniture_colors = {registry.id_to_rgb[sid] for sid in registry.object_ids}
    arr = np.array(Image.open(image_path).convert("RGB"), dtype=np.uint8)
    arch = json.loads(architecture_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path and manifest_path.exists() else {}
    objects = []
    for rgb in sorted(furniture_colors):
        mask = (arr == np.array(rgb, dtype=np.uint8)).all(axis=2)
        for idx, (x0, y0, x1, y1, area, cx, cy) in enumerate(_component_bfs(mask)):
            if area < min_area:
                continue
            wx, wy, mode = _pixel_to_world(cx, cy, arch)
            wx0, wy0, _ = _pixel_to_world(x0, y0, arch)
            wx1, wy1, _ = _pixel_to_world(x1, y1, arch)
            size_m = None
            if None not in (wx0, wy0, wx1, wy1):
                size_m = [abs(float(wx1) - float(wx0)), abs(float(wy1) - float(wy0))]
            objects.append(
                {
                    "instance_id": f"parsed_{rgb_to_cat[rgb]}_{len(objects):04d}",
                    "category": rgb_to_cat[rgb],
                    "bbox_px": [int(x0), int(y0), int(x1), int(y1)],
                    "centroid_px": [cx, cy],
                    "pixel_area": int(area),
                    "center_m": [wx, wy] if wx is not None and wy is not None else None,
                    "size_m": size_m,
                    "orientation_deg": 0,
                    "parse_transform_mode": mode,
                }
            )
    return {
        "schema_version": "layout-json-v1",
        "layout_id": f"parsed_{image_path.stem}",
        "sample_id": manifest.get("sample_id") or image_path.stem.replace("_quantized", ""),
        "source": {
            "kind": "qwen_semantic_furniture_parse",
            "architecture_source_of_truth": "raw_3dfront",
            "qwen_generates_furniture_only": True,
            "parse_transform_mode": "metric_transform" if isinstance(arch.get("metric_transform"), dict) else "implicit_polygon_bbox_fallback",
            "source_image": str(image_path),
            "architecture_json": str(architecture_path),
        },
        "objects": objects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("architecture", type=Path)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-area", type=int, default=4)
    args = parser.parse_args()
    result = parse_output(args.image, args.architecture, args.manifest, args.min_area)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
