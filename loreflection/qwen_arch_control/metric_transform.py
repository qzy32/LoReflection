"""Metric canvas transform for Qwen Architecture In-Context rendering.

Raw 3D-FRONT JSON remains the architecture source of truth. Qwen generates
furniture semantic pixels only; those pixels must be inverse-transformed with
this explicit metric transform before layout write-back.
"""

from __future__ import annotations

from typing import Any


def _bbox(points: list[list[float]]) -> tuple[float, float, float, float]:
    if not points:
        raise ValueError("room_points_m must not be empty")
    xs = [float(p[0]) for p in points]
    zs = [float(p[1]) for p in points]
    return min(xs), min(zs), max(xs), max(zs)


def build_metric_transform(
    room_points_m: list[list[float]],
    image_size_px: int = 256,
    canvas_extent_m: float | None = None,
    pixels_per_meter: float | None = None,
    policy: str = "fixed_metric_canvas",
) -> dict[str, Any]:
    if policy != "fixed_metric_canvas":
        raise ValueError(f"unsupported metric transform policy: {policy}")
    x0, z0, x1, z1 = _bbox(room_points_m)
    room_w = max(1e-6, x1 - x0)
    room_d = max(1e-6, z1 - z0)
    needed = max(room_w, room_d)
    extent = float(canvas_extent_m or 8.0)
    if needed > extent:
        extent = 10.0 if needed <= 10.0 else 12.0 if needed <= 12.0 else float(needed * 1.05)
    ppm = float(pixels_per_meter or (image_size_px / extent))
    # Center the real room in the fixed metric canvas; top-left world origin is explicit.
    cx = (x0 + x1) / 2.0
    cz = (z0 + z1) / 2.0
    origin_x = cx - extent / 2.0
    origin_z = cz - extent / 2.0
    return {
        "schema_version": "metric-transform-v1",
        "scale_policy": policy,
        "image_size_px": [int(image_size_px), int(image_size_px)],
        "canvas_extent_m": extent,
        "pixels_per_meter": ppm,
        "origin_world_m": [origin_x, origin_z],
        "room_center_world_m": [cx, cz],
        "room_bbox_m": [x0, z0, x1, z1],
        "x_axis_direction": "right",
        "y_axis_direction": "down",
    }


def world_to_pixel(point_m: tuple[float, float], transform: dict[str, Any]) -> tuple[int, int]:
    ppm = float(transform["pixels_per_meter"])
    ox, oz = [float(v) for v in transform["origin_world_m"]]
    size = int(transform["image_size_px"][0])
    x = round((float(point_m[0]) - ox) * ppm)
    y = round((float(point_m[1]) - oz) * ppm)
    return max(0, min(size - 1, int(x))), max(0, min(size - 1, int(y)))


def pixel_to_world(point_px: tuple[float, float], transform: dict[str, Any]) -> tuple[float, float]:
    ppm = float(transform["pixels_per_meter"])
    ox, oz = [float(v) for v in transform["origin_world_m"]]
    x = ox + float(point_px[0]) / ppm
    z = oz + float(point_px[1]) / ppm
    return float(x), float(z)
