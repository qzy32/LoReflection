"""Palette-exact top-down renderer for the full semantic Qwen mainline.

Official outputs from this module are semantic images for model input/training.
They must not contain alpha, anti-aliasing, debug colors, text, or non-registry
RGB values. Human inspection overlays belong in reports only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import hashlib
import json
import math

import numpy as np
from PIL import Image, ImageDraw

from loreflection.qwen_arch_control.metric_transform import world_to_pixel
from loreflection.semantic_registry import SemanticRegistry, load_registry

PROTECTED_CATEGORY_NAMES = ("void", "door", "window", "wall", "clearance", "non_placeable")
OPENING_CATEGORY_NAMES = {"door", "window"}


def _rgb(registry: SemanticRegistry, name: str) -> tuple[int, int, int] | None:
    return registry.name_to_rgb.get(name)


def _draw_polygon(draw: ImageDraw.ImageDraw, points, fill: tuple[int, int, int]) -> None:
    if len(points) >= 3:
        draw.polygon([(int(round(x)), int(round(y))) for x, y in points], fill=fill)


def _bbox_points(bbox) -> list[tuple[int, int]]:
    x0, y0, x1, y1 = [int(round(v)) for v in bbox]
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _clamp_bbox(x0: int, y0: int, x1: int, y1: int, size: int) -> list[int]:
    return [max(0, min(size - 1, x0)), max(0, min(size - 1, y0)), max(0, min(size - 1, x1)), max(0, min(size - 1, y1))]


def _opening_min_px_for_target_size(size: int) -> int:
    return max(3, int(round(size / 128)))


def _expand_opening_bbox(points: list[tuple[int, int]], size: int) -> tuple[list[tuple[int, int]], bool]:
    if not points:
        return points, False
    min_px = _opening_min_px_for_target_size(size)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    changed = False
    if x1 - x0 + 1 < min_px:
        c = round((x0 + x1) / 2)
        half = min_px // 2
        x0, x1 = c - half, c + (min_px - half - 1)
        changed = True
    if y1 - y0 + 1 < min_px:
        c = round((y0 + y1) / 2)
        half = min_px // 2
        y0, y1 = c - half, c + (min_px - half - 1)
        changed = True
    x0, y0, x1, y1 = _clamp_bbox(x0, y0, x1, y1, size)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], changed


def _anchor_points(anchor: dict[str, Any], transform: dict[str, Any] | None, size: int) -> tuple[list[tuple[int, int]], str]:
    if anchor.get("bbox_m") and transform:
        x0, z0, x1, z1 = [float(v) for v in anchor["bbox_m"]]
        p0 = world_to_pixel((x0, z0), transform)
        p1 = world_to_pixel((x1, z1), transform)
        bbox = [min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])]
        return _bbox_points(_clamp_bbox(*bbox, size)), "bbox_m_metric_transform"
    if anchor.get("polygon_m") and transform:
        return [world_to_pixel((float(x), float(z)), transform) for x, z in anchor["polygon_m"]], "polygon_m_metric_transform"
    if anchor.get("polygon_px"):
        return [(int(round(x)), int(round(y))) for x, y in anchor["polygon_px"]], "polygon_px"
    if anchor.get("bbox_px"):
        return _bbox_points(anchor["bbox_px"]), "bbox_px"
    return [], "missing_anchor_geometry"


def _boundary_points(architecture: dict[str, Any], transform: dict[str, Any] | None) -> tuple[list[tuple[int, int]], str]:
    boundary = architecture.get("boundary") or {}
    if boundary.get("polygon_m") and transform:
        return [world_to_pixel((float(x), float(z)), transform) for x, z in boundary["polygon_m"]], "polygon_m_metric_transform"
    if boundary.get("polygon_px"):
        return [(int(round(x)), int(round(y))) for x, y in boundary["polygon_px"]], "polygon_px"
    return [], "missing_boundary"


def _transform_debug(architecture: dict[str, Any], size: int) -> dict[str, Any]:
    transform = architecture.get("metric_transform") or {}
    ppm = float(transform.get("pixels_per_meter") or 0.0)
    payload = json.dumps(transform, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {
        "metric_transform_exists": bool(transform),
        "metric_transform_hash": hashlib.sha256(payload).hexdigest() if transform else None,
        "room_bbox_m": transform.get("room_bbox_m"),
        "pixels_per_meter": ppm or None,
        "pixels_per_cm": (ppm / 100.0) if ppm else None,
        "cm_per_pixel": (100.0 / ppm) if ppm else None,
        "canvas_w": size,
        "canvas_h": size,
        "pad_left": 0,
        "pad_top": 0,
        "target_size": [size, size],
        "local_crop_enabled": False,
        "crop_policy": "fixed_metric_canvas_from_architecture_metric_transform",
        "nearest_neighbor_semantic_resize": False,
        "source_transform_schema": transform.get("schema_version"),
    }


def _wall_status(architecture: dict[str, Any], registry: SemanticRegistry) -> dict[str, Any]:
    wall_in_registry = "wall" in registry.name_to_rgb
    anchors = architecture.get("anchors", []) or []
    wall_in_arch = any(str(a.get("anchor_type", "")).lower() == "wall" for a in anchors)
    for key in ("wall", "walls", "wall_mesh", "wall_meshes"):
        if architecture.get(key):
            wall_in_arch = True
    source = architecture.get("source") or {}
    wall_source_mesh_available = bool(source.get("wall_mesh") or source.get("wall_meshes") or source.get("walls"))
    if wall_in_registry:
        policy = "wall_class_rendered"
    elif wall_in_arch or wall_source_mesh_available:
        policy = "wall_geometry_available_but_no_palette_class"
    else:
        policy = "no_wall_class_floor_void_boundary_only"
    return {
        "wall_in_registry": wall_in_registry,
        "wall_in_architecture_json": wall_in_arch,
        "wall_source_mesh_available": wall_source_mesh_available,
        "wall_rendering_policy": policy,
    }


def _footprint_to_px(obj: dict[str, Any], transform: dict[str, Any] | None) -> tuple[list[tuple[int, int]], str, bool]:
    if obj.get("footprint_m") and transform:
        return [world_to_pixel((float(x), float(z)), transform) for x, z in obj["footprint_m"]], "footprint_m_oriented", False
    if obj.get("footprint_px"):
        return [(int(round(x)), int(round(y))) for x, y in obj["footprint_px"]], "footprint_px", False
    if obj.get("center_m") and obj.get("size_m") and transform:
        cx, cz = [float(v) for v in obj["center_m"][:2]]
        sx, sz = [float(v) for v in obj["size_m"][:2]]
        angle = math.radians(float(obj.get("orientation_deg", 0.0)))
        corners = [(-sx / 2, -sz / 2), (sx / 2, -sz / 2), (sx / 2, sz / 2), (-sx / 2, sz / 2)]
        pts_m = []
        for dx, dz in corners:
            rx = dx * math.cos(angle) - dz * math.sin(angle)
            rz = dx * math.sin(angle) + dz * math.cos(angle)
            pts_m.append((cx + rx, cz + rz))
        return [world_to_pixel(pt, transform) for pt in pts_m], "center_size_orientation", False
    if obj.get("bbox_px"):
        return _bbox_points(obj["bbox_px"]), "bbox_px_fallback", True
    return [], "missing_geometry", True


def render_architecture_condition_image(
    architecture: dict[str, Any],
    output_path: str | Path | None = None,
    *,
    registry: SemanticRegistry | None = None,
    image_size_px: int | None = None,
) -> tuple[Image.Image, dict[str, Any]]:
    registry = registry or load_registry()
    size = image_size_px or int((architecture.get("image_size_px") or [256, 256])[0])
    transform = architecture.get("metric_transform")
    void_rgb = _rgb(registry, "void") or (0, 0, 0)
    floor_rgb = _rgb(registry, "floor") or (255, 255, 255)
    img = Image.new("RGB", (size, size), void_rgb)
    draw = ImageDraw.Draw(img)
    boundary_px, boundary_source = _boundary_points(architecture, transform)
    if boundary_px:
        _draw_polygon(draw, boundary_px, floor_rgb)

    anchor_reports: list[dict[str, Any]] = []
    for anchor in architecture.get("anchors", []) or []:
        kind = str(anchor.get("anchor_type", "")).lower()
        color = _rgb(registry, kind)
        if color is None:
            continue
        pts, source = _anchor_points(anchor, transform, size)
        min_visible_applied = False
        if kind in OPENING_CATEGORY_NAMES:
            pts, min_visible_applied = _expand_opening_bbox(pts, size)
        before = np.asarray(img).copy()
        if pts:
            _draw_polygon(draw, pts, color)
        after = np.asarray(img)
        pixels = int(np.count_nonzero(np.any(before != after, axis=2)))
        anchor_reports.append({
            "anchor_id": anchor.get("anchor_id"),
            "anchor_type": kind,
            "geometry_source": source,
            "pixel_count": pixels,
            "min_visible_strip_applied": min_visible_applied,
        })

    wall = _wall_status(architecture, registry)
    report = {
        "renderer": "semantic_topdown_renderer_v2",
        "image_size_px": [size, size],
        "palette_exact": True,
        "architecture_only": True,
        "boundary_source": boundary_source,
        "transform_debug": _transform_debug(architecture, size),
        **wall,
        "anchor_counts": {k: sum(1 for a in architecture.get("anchors", []) or [] if str(a.get("anchor_type", "")).lower() == k) for k in ("door", "window")},
        "anchor_pixel_counts": {k: sum(r["pixel_count"] for r in anchor_reports if r["anchor_type"] == k) for k in ("door", "window")},
        "anchor_reports": anchor_reports,
        "opening_min_visible_px": _opening_min_px_for_target_size(size),
        "no_alpha": True,
        "no_antialiasing": True,
        "official_qwen_input": True,
    }
    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
    return img, report


def render_full_semantic_target_image(
    architecture: dict[str, Any],
    layout: dict[str, Any],
    target_output_path: str | Path | None = None,
    *,
    context_output_path: str | Path | None = None,
    registry: SemanticRegistry | None = None,
    image_size_px: int | None = None,
) -> tuple[Image.Image, dict[str, Any]]:
    registry = registry or load_registry()
    context_img, context_report = render_architecture_condition_image(
        architecture, context_output_path, registry=registry, image_size_px=image_size_px
    )
    context = np.asarray(context_img)
    target = context.copy()
    size = target.shape[0]
    floor_rgb = _rgb(registry, "floor")
    void_rgb = _rgb(registry, "void")
    door_rgb = _rgb(registry, "door")
    window_rgb = _rgb(registry, "window")
    protected_rgbs = [rgb for name in PROTECTED_CATEGORY_NAMES if (rgb := _rgb(registry, name)) is not None]
    floor_mask = np.all(context == floor_rgb, axis=2) if floor_rgb is not None else np.zeros((size, size), dtype=bool)
    void_mask = np.all(context == void_rgb, axis=2) if void_rgb is not None else np.zeros((size, size), dtype=bool)
    door_mask = np.all(context == door_rgb, axis=2) if door_rgb is not None else np.zeros((size, size), dtype=bool)
    window_mask = np.all(context == window_rgb, axis=2) if window_rgb is not None else np.zeros((size, size), dtype=bool)
    protected_mask = np.zeros((size, size), dtype=bool)
    for color in protected_rgbs:
        protected_mask |= np.all(context == color, axis=2)

    transform = architecture.get("metric_transform") or layout.get("metric_transform")
    transform_hash = context_report["transform_debug"].get("metric_transform_hash")
    written_mask = np.zeros((size, size), dtype=bool)
    object_reports = []
    for obj in layout.get("objects", []) or []:
        category = obj.get("category")
        color = _rgb(registry, str(category)) if category else None
        points, render_source, fallback_used = _footprint_to_px(obj, transform)
        if color is None or len(points) < 3:
            object_reports.append({
                "instance_id": obj.get("instance_id"), "category": category, "render_source": render_source,
                "raw_object_area_px": 0, "written_area_px": 0, "clipped_area_px": 0, "clipped_ratio": 1.0,
                "void_overlap_px": 0, "door_overlap_px": 0, "window_overlap_px": 0, "protected_overlap_px": 0,
                "outside_image_px": 0, "already_occupied_px": 0, "fallback_used": fallback_used,
                "decision": "hard_fail", "reason": "missing_palette_or_geometry",
            })
            continue
        mask_img = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask_img).polygon(points, fill=255)
        object_mask = np.asarray(mask_img) > 0
        raw_area = int(object_mask.sum())
        allowed_mask = object_mask & floor_mask & ~written_mask
        void_overlap = int((object_mask & void_mask).sum())
        door_overlap = int((object_mask & door_mask).sum())
        window_overlap = int((object_mask & window_mask).sum())
        protected_overlap = int((object_mask & protected_mask).sum())
        already_occupied = int((object_mask & written_mask).sum())
        outside_image = int(any(x < 0 or y < 0 or x >= size or y >= size for x, y in points))
        written_area = int(allowed_mask.sum())
        clipped_area = max(raw_area - written_area, 0)
        if written_area > 0:
            target[allowed_mask] = color
            written_mask |= allowed_mask
        decision = "written" if written_area == raw_area else ("clipped" if written_area > 0 else "hard_fail")
        object_reports.append({
            "instance_id": obj.get("instance_id"), "category": category, "render_source": render_source,
            "raw_object_area_px": raw_area, "written_area_px": written_area,
            "clipped_area_px": clipped_area, "clipped_ratio": (clipped_area / raw_area) if raw_area else 1.0,
            "void_overlap_px": void_overlap, "door_overlap_px": door_overlap, "window_overlap_px": window_overlap,
            "protected_overlap_px": protected_overlap, "outside_image_px": outside_image,
            "already_occupied_px": already_occupied, "fallback_used": fallback_used,
            "decision": decision, "reason": "ok" if decision == "written" else "outside_floor_or_protected_or_overlap",
        })

    protected_pixels_unchanged = bool(np.array_equal(context[protected_mask], target[protected_mask]))
    img = Image.fromarray(target.astype(np.uint8))
    if target_output_path is not None:
        Path(target_output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(target_output_path)
    report = {
        "renderer": "semantic_topdown_renderer_v2",
        "image_size_px": [size, size],
        "palette_exact": True,
        "target_kind": "full_semantic",
        "target_base": "qwen_input_byte_copy_then_furniture_overlay",
        "context_target_same_shape": list(context.shape) == list(target.shape),
        "context_target_same_transform_hash": True,
        "metric_transform_hash": transform_hash,
        "protected_pixels_unchanged": protected_pixels_unchanged,
        "protected_pixels_changed_count": 0 if protected_pixels_unchanged else int(np.count_nonzero(np.any(context[protected_mask] != target[protected_mask], axis=1))),
        "context_report": context_report,
        "object_reports": object_reports,
        "num_objects": len(object_reports),
        "zero_written_object_count": sum(1 for r in object_reports if r["written_area_px"] == 0),
        "clipped_object_count": sum(1 for r in object_reports if r["clipped_area_px"] > 0),
        "fallback_object_count": sum(1 for r in object_reports if r["fallback_used"]),
        "furniture_on_void_pixels_after_write": 0,
        "furniture_on_protected_pixels_after_write": 0,
        "door_window_overwritten_pixels_after_write": 0,
        "write_policy": "furniture_pixels_write_to_floor_only",
        "wall_rendering_policy": context_report["wall_rendering_policy"],
    }
    return img, report
