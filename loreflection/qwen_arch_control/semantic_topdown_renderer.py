"""Palette-exact top-down renderer for the full semantic Qwen mainline.

This renderer is the only current mainline target renderer: it renders an
architecture condition image and a full semantic supervised target. Furniture
semantic pixels are allowed to overwrite floor pixels only. Void and protected
architecture pixels are kept unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import math
import numpy as np
from PIL import Image, ImageDraw

from loreflection.semantic_registry import SemanticRegistry, load_registry
from loreflection.qwen_arch_control.metric_transform import world_to_pixel

PROTECTED_CATEGORY_NAMES = ("void", "door", "window", "wall", "clearance", "non_placeable")


def _rgb(registry: SemanticRegistry, name: str) -> tuple[int, int, int] | None:
    try:
        return registry.name_to_rgb[name]
    except KeyError:
        return None


def _draw_polygon(draw: ImageDraw.ImageDraw, points, fill: tuple[int, int, int]) -> None:
    if len(points) >= 3:
        draw.polygon([(int(round(x)), int(round(y))) for x, y in points], fill=fill)


def _bbox_points(bbox) -> list[tuple[int, int]]:
    x0, y0, x1, y1 = [int(round(v)) for v in bbox]
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _footprint_to_px(obj: dict[str, Any], transform: dict[str, Any] | None) -> tuple[list[tuple[int, int]], str]:
    if obj.get("footprint_m") and transform:
        return [world_to_pixel((float(x), float(z)), transform) for x, z in obj["footprint_m"]], "footprint_m_oriented"
    if obj.get("footprint_px"):
        return [(int(round(x)), int(round(y))) for x, y in obj["footprint_px"]], "footprint_px"
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
        return [world_to_pixel(pt, transform) for pt in pts_m], "center_size_orientation"
    if obj.get("bbox_px"):
        return _bbox_points(obj["bbox_px"]), "bbox_px_fallback"
    return [], "missing_geometry"


def render_architecture_condition_image(
    architecture: dict[str, Any],
    output_path: str | Path | None = None,
    *,
    registry: SemanticRegistry | None = None,
    image_size_px: int | None = None,
) -> tuple[Image.Image, dict[str, Any]]:
    registry = registry or load_registry()
    size = image_size_px or int((architecture.get("image_size_px") or [256, 256])[0])
    void_rgb = _rgb(registry, "void") or (0, 0, 0)
    floor_rgb = _rgb(registry, "floor") or (255, 255, 255)
    img = Image.new("RGB", (size, size), void_rgb)
    draw = ImageDraw.Draw(img)
    polygon_px = (architecture.get("boundary") or {}).get("polygon_px") or []
    if polygon_px:
        _draw_polygon(draw, polygon_px, floor_rgb)

    anchor_pixel_counts: dict[str, int] = {}
    for anchor in architecture.get("anchors", []) or []:
        kind = str(anchor.get("anchor_type", "")).lower()
        color = _rgb(registry, kind)
        if color is None:
            if kind in {"clearance", "non_placeable"}:
                color = floor_rgb
            else:
                continue
        pts = anchor.get("polygon_px") or (_bbox_points(anchor["bbox_px"]) if anchor.get("bbox_px") else [])
        before = np.asarray(img).copy()
        if pts:
            _draw_polygon(draw, pts, color)
        after = np.asarray(img)
        anchor_pixel_counts[kind] = anchor_pixel_counts.get(kind, 0) + int(np.count_nonzero(np.any(before != after, axis=2)))

    report = {
        "renderer": "semantic_topdown_renderer_v1",
        "image_size_px": [size, size],
        "palette_exact": True,
        "architecture_only": True,
        "wall_in_registry": _rgb(registry, "wall") is not None,
        "wall_representation": "floor_void_boundary" if _rgb(registry, "wall") is None else "explicit_palette_class",
        "anchor_counts": {k: sum(1 for a in architecture.get("anchors", []) or [] if str(a.get("anchor_type", "")).lower() == k) for k in ("door", "window")},
        "anchor_pixel_counts": anchor_pixel_counts,
        "boundary_source": (architecture.get("boundary") or {}).get("boundary_source") or (architecture.get("boundary") or {}).get("source"),
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
    protected_rgbs = [rgb for name in PROTECTED_CATEGORY_NAMES if (rgb := _rgb(registry, name)) is not None]
    floor_mask = np.all(context == floor_rgb, axis=2) if floor_rgb is not None else np.zeros((size, size), dtype=bool)
    void_mask = np.all(context == void_rgb, axis=2) if void_rgb is not None else np.zeros((size, size), dtype=bool)
    protected_mask = np.zeros((size, size), dtype=bool)
    for color in protected_rgbs:
        protected_mask |= np.all(context == color, axis=2)

    transform = architecture.get("metric_transform") or layout.get("metric_transform")
    written_mask = np.zeros((size, size), dtype=bool)
    object_reports = []
    for obj in layout.get("objects", []) or []:
        category = obj.get("category")
        color = _rgb(registry, str(category)) if category else None
        points, render_source = _footprint_to_px(obj, transform)
        if color is None or len(points) < 3:
            object_reports.append({
                "instance_id": obj.get("instance_id"), "category": category, "render_source": render_source,
                "raw_object_area_px": 0, "written_area_px": 0, "clipped_area_px": 0, "clipped_ratio": 1.0,
                "void_overlap_px": 0, "protected_overlap_px": 0, "already_occupied_px": 0,
                "decision": "hard_fail", "reason": "missing_palette_or_geometry",
            })
            continue
        mask_img = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask_img).polygon(points, fill=255)
        object_mask = np.asarray(mask_img) > 0
        raw_area = int(object_mask.sum())
        allowed_mask = object_mask & floor_mask & ~written_mask
        void_overlap = int((object_mask & void_mask).sum())
        protected_overlap = int((object_mask & protected_mask).sum())
        already_occupied = int((object_mask & written_mask).sum())
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
            "void_overlap_px": void_overlap, "protected_overlap_px": protected_overlap,
            "already_occupied_px": already_occupied,
            "decision": decision, "reason": "ok" if decision == "written" else "outside_floor_or_protected_or_overlap",
        })

    img = Image.fromarray(target.astype(np.uint8), "RGB")
    if target_output_path is not None:
        Path(target_output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(target_output_path)
    report = {
        "renderer": "semantic_topdown_renderer_v1",
        "image_size_px": [size, size],
        "palette_exact": True,
        "target_kind": "full_semantic",
        "context_report": context_report,
        "object_reports": object_reports,
        "num_objects": len(object_reports),
        "zero_written_object_count": sum(1 for r in object_reports if r["written_area_px"] == 0),
        "clipped_object_count": sum(1 for r in object_reports if r["clipped_area_px"] > 0),
        "furniture_on_void_pixels_after_write": 0,
        "furniture_on_protected_pixels_after_write": 0,
        "door_window_overwritten_pixels_after_write": 0,
        "write_policy": "furniture_pixels_write_to_floor_only",
        "wall_representation": context_report["wall_representation"],
    }
    return img, report
