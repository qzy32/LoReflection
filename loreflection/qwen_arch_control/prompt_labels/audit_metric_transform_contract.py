from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image

from loreflection.qwen_arch_control.metric_transform import pixel_to_world, world_to_pixel


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rate(n: int, d: int) -> float | None:
    return None if d == 0 else n / d


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = min(len(values) - 1, math.ceil(0.95 * len(values)) - 1)
    return values[index]


def _candidate_architecture_paths(base: Path, row: dict[str, str]) -> list[Path]:
    sample_id = row.get("sample_id", "")
    candidates = [base / "meta" / f"{sample_id}_architecture.json"]
    for key in ("image", "context_image", "goal_lostate", "prompt_package", "verifier_refs"):
        value = row.get(key)
        if not value:
            continue
        resolved = (base / value).resolve()
        # metadata rows may point from a prompt-label dataset back to the source
        # metric_v2 dataset through ../loreflection_qwen_arch_control_p1_small_metric_v2.
        candidates.append(resolved.parents[1] / "meta" / f"{sample_id}_architecture.json")
        candidates.append(resolved.parent.parent / "meta" / f"{sample_id}_architecture.json")
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = path.as_posix()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def resolve_architecture_path(base: Path, row: dict[str, str]) -> Path | None:
    for path in _candidate_architecture_paths(base, row):
        if path.exists():
            return path
    return None


def audit_metric_transform_contract(metadata_path: str | Path, dataset_base: str | Path) -> dict[str, Any]:
    metadata = Path(metadata_path)
    base = Path(dataset_base)
    rows = list(csv.DictReader(metadata.open(encoding="utf-8"))) if metadata.exists() else []
    total = len(rows)
    same_resolution = 0
    size_256 = 0
    metric_exists = 0
    fallback = 0
    ppm_values: list[float] = []
    roundtrip_errors: list[float] = []
    sample_rows: list[dict[str, Any]] = []
    for row in rows:
        image_path = base / row.get("image", "")
        context_path = base / row.get("context_image", "")
        image_size = None
        context_size = None
        if image_path.exists():
            image_size = Image.open(image_path).size
        if context_path.exists():
            context_size = Image.open(context_path).size
        if image_size and context_size and image_size == context_size:
            same_resolution += 1
        if image_size == (256, 256) and context_size == (256, 256):
            size_256 += 1
        arch_path = resolve_architecture_path(base, row)
        if arch_path:
            arch = _read_json(arch_path)
            transform = arch.get("metric_transform")
            if transform:
                metric_exists += 1
                ppm = float(transform.get("pixels_per_meter", 0.0))
                if ppm:
                    ppm_values.append(ppm)
                bbox = transform.get("room_bbox_m") or [0, 0, 1, 1]
                points = [(bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])]
                for point in points:
                    px = world_to_pixel(point, transform)
                    back = pixel_to_world(px, transform)
                    roundtrip_errors.append(math.dist(point, back))
            else:
                fallback += 1
            if len(sample_rows) < 5:
                sample_rows.append({
                    "sample_id": row.get("sample_id"),
                    "image_size": image_size,
                    "context_size": context_size,
                    "architecture_keys": sorted(arch.keys()),
                    "metric_transform": transform or None,
                })
    stable_ppm = len(set(round(v, 6) for v in ppm_values)) <= 3 if ppm_values else None
    return {
        "metadata_path": metadata.as_posix(),
        "dataset_base": base.as_posix(),
        "num_rows": total,
        "same_resolution_rate": _rate(same_resolution, total),
        "all_images_256x256_rate": _rate(size_256, total),
        "metric_transform_exists_rate": _rate(metric_exists, total),
        "normalized_v1_or_missing_transform_rate": _rate(fallback, total),
        "pixels_per_meter_values": sorted(set(round(v, 6) for v in ppm_values)),
        "pixels_per_meter_min": min(ppm_values) if ppm_values else None,
        "pixels_per_meter_max": max(ppm_values) if ppm_values else None,
        "pixels_per_meter_stable": stable_ppm,
        "meters_per_pixel_values": sorted(set(round(1.0 / v, 8) for v in ppm_values if v)),
        "roundtrip_error_p95_m": _p95(roundtrip_errors),
        "context_and_target_share_transform": True if metric_exists == total and total else None,
        "wrong_scaling_risk": bool(fallback or stable_ppm is False),
        "sample_architecture_keys": sample_rows,
    }
