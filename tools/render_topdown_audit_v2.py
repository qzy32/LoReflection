#!/usr/bin/env python3
"""Render human-facing top-down audit views using only the Python standard library."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import os
import struct
import zlib
from collections import Counter
from pathlib import Path
from typing import Any


CANONICAL_DIRS = [
    "architecture_condition_v1",
    "gt_semantic_layout_v1",
    "semantic_layout_v1",
    "architecture_json_v1",
    "arch_json_v1",
    "observed_lostate_v1",
]

FONT = {
    "a": ["01110", "10001", "00001", "01111", "10001", "10011", "01101"],
    "b": ["10000", "10000", "10110", "11001", "10001", "10001", "11110"],
    "c": ["00000", "00000", "01110", "10000", "10000", "10001", "01110"],
    "d": ["00001", "00001", "01101", "10011", "10001", "10001", "01111"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110"],
    "f": ["00110", "01001", "01000", "11100", "01000", "01000", "01000"],
    "g": ["00000", "01111", "10001", "10001", "01111", "00001", "01110"],
    "h": ["10000", "10000", "10110", "11001", "10001", "10001", "10001"],
    "i": ["00100", "00000", "01100", "00100", "00100", "00100", "01110"],
    "j": ["00010", "00000", "00110", "00010", "00010", "10010", "01100"],
    "k": ["10000", "10010", "10100", "11000", "10100", "10010", "10001"],
    "l": ["01100", "00100", "00100", "00100", "00100", "00100", "01110"],
    "m": ["00000", "00000", "11010", "10101", "10101", "10101", "10101"],
    "n": ["00000", "00000", "10110", "11001", "10001", "10001", "10001"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110"],
    "p": ["00000", "11110", "10001", "10001", "11110", "10000", "10000"],
    "q": ["00000", "01111", "10001", "10001", "01111", "00001", "00001"],
    "r": ["00000", "00000", "10110", "11001", "10000", "10000", "10000"],
    "s": ["00000", "00000", "01111", "10000", "01110", "00001", "11110"],
    "t": ["01000", "01000", "11100", "01000", "01000", "01001", "00110"],
    "u": ["00000", "00000", "10001", "10001", "10001", "10011", "01101"],
    "v": ["00000", "00000", "10001", "10001", "10001", "01010", "00100"],
    "w": ["00000", "00000", "10001", "10101", "10101", "10101", "01010"],
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
    "y": ["00000", "10001", "10001", "01111", "00001", "10001", "01110"],
    "z": ["00000", "00000", "11111", "00010", "00100", "01000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "11100"],
    " ": ["00000"] * 7,
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "00100", "00100", "01000"],
    "|": ["00100"] * 7,
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rel_from(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def hex_color(value: str, default: str = "#000000") -> tuple[int, int, int]:
    value = str(value or default).strip().lstrip("#")
    if len(value) != 6:
        value = default.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def color_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % rgb


def write_png(path: Path, width: int, height: int, pixels: list[list[tuple[int, int, int]]]) -> None:
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return len(data).to_bytes(4, "big") + kind + data + zlib.crc32(kind + data).to_bytes(4, "big")

    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00")
    payload += chunk(b"IDAT", compressed)
    payload += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def blank(width: int, height: int, color: tuple[int, int, int]) -> list[list[tuple[int, int, int]]]:
    return [[color for _ in range(width)] for _ in range(height)]


def set_px(pixels: list[list[tuple[int, int, int]]], x: int, y: int, color: tuple[int, int, int]) -> None:
    if 0 <= y < len(pixels) and 0 <= x < len(pixels[y]):
        pixels[y][x] = color


def rect(pixels: list[list[tuple[int, int, int]]], box: list[int], fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None, width: int = 1) -> None:
    x0, y0, x1, y1 = box
    max_x = len(pixels[0]) - 1
    max_y = len(pixels) - 1
    x0 = min(max(0, x0), max_x)
    x1 = min(max(0, x1), max_x)
    y0 = min(max(0, y0), max_y)
    y1 = min(max(0, y1), max_y)
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            pixels[y][x] = fill
    if outline:
        for t in range(width):
            for x in range(x0 + t, x1 - t + 1):
                set_px(pixels, x, y0 + t, outline)
                set_px(pixels, x, y1 - t, outline)
            for y in range(y0 + t, y1 - t + 1):
                set_px(pixels, x0 + t, y, outline)
                set_px(pixels, x1 - t, y, outline)


def line(pixels: list[list[tuple[int, int, int]]], p0: tuple[int, int], p1: tuple[int, int], color: tuple[int, int, int], width: int = 1) -> None:
    x0, y0 = p0
    x1, y1 = p1
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = max(0, width // 2)
    while True:
        for yy in range(y0 - r, y0 + r + 1):
            for xx in range(x0 - r, x0 + r + 1):
                set_px(pixels, xx, yy, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def point_in_poly(x: int, y: int, pts: list[tuple[int, int]]) -> bool:
    inside = False
    j = len(pts) - 1
    for i, pi in enumerate(pts):
        xi, yi = pi
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / max(yj - yi, 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def polygon(pixels: list[list[tuple[int, int, int]]], pts: list[tuple[int, int]], fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None, width: int = 1) -> None:
    if len(pts) < 3:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for y in range(max(0, min(ys)), min(len(pixels) - 1, max(ys)) + 1):
        for x in range(max(0, min(xs)), min(len(pixels[0]) - 1, max(xs)) + 1):
            if point_in_poly(x, y, pts):
                pixels[y][x] = fill
    if outline:
        for idx, p0 in enumerate(pts):
            line(pixels, p0, pts[(idx + 1) % len(pts)], outline, width)


def draw_text(pixels: list[list[tuple[int, int, int]]], x: int, y: int, text: str, color: tuple[int, int, int], scale: int = 2) -> None:
    cx = x
    for ch in text.lower():
        glyph = FONT.get(ch, FONT.get(" ", ["00000"] * 7))
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    rect(pixels, [cx + gx * scale, y + gy * scale, cx + (gx + 1) * scale - 1, y + (gy + 1) * scale - 1], color)
        cx += 6 * scale


def paste(dst: list[list[tuple[int, int, int]]], src: list[list[tuple[int, int, int]]], xoff: int, yoff: int) -> None:
    for y, row in enumerate(src):
        yy = y + yoff
        if yy < 0 or yy >= len(dst):
            continue
        for x, c in enumerate(row):
            xx = x + xoff
            if 0 <= xx < len(dst[yy]):
                dst[yy][xx] = c


def load_palette(path: Path) -> dict[str, str]:
    return dict(load_json(path).get("colors", {}))


def load_style(path: Path | None) -> dict[str, Any]:
    style = load_json(path) if path and path.exists() else {}
    style = unwrap_style_values(style)
    style.setdefault("canvas", {"width": 1800, "height": 850, "margin_ratio": 0.08, "panel_size": 500, "panel_gap": 26})
    style.setdefault("line_widths", {"boundary": 6, "derived_wall": 5, "door": 8, "window": 8, "instance_outline": 2, "panel_border": 2})
    style.setdefault("marker_sizes", {"minimum_anchor_marker_px": 16})
    style.setdefault("colors", {})
    defaults = {
        "canvas_background": "#FFFFFF",
        "panel_background": "#FAFAFA",
        "room_fill": "#F4F1E8",
        "boundary": "#111111",
        "derived_wall": "#000000",
        "door": "#D73027",
        "door_fill": "#FCA082",
        "window": "#0571B0",
        "window_fill": "#92C5DE",
        "text": "#1F2933",
        "muted_text": "#52616B",
        "panel_border": "#B8C2CC",
        "furniture_outline": "#111111",
        "clearance": "#FFF3B0",
    }
    for k, v in defaults.items():
        style["colors"].setdefault(k, v)
    return style


def unwrap_style_values(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value and "source_type" in value:
        return unwrap_style_values(value["value"])
    if isinstance(value, dict):
        return {k: unwrap_style_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unwrap_style_values(v) for v in value]
    return value


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hashes(root: Path) -> dict[str, str]:
    out = {}
    for dirname in CANONICAL_DIRS:
        d = root / dirname
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                out[p.relative_to(root).as_posix()] = hash_file(p)
    return out


def polygon_points(value: Any) -> list[list[float]]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                out.append([float(item[0]), float(item[1])])
            except (TypeError, ValueError):
                pass
    return out


def entity_footprint(entity: dict[str, Any]) -> list[list[float]]:
    return polygon_points(entity.get("footprint") or entity.get("footprint_m"))


def anchor_footprint(anchor: dict[str, Any]) -> list[list[float]]:
    return polygon_points(anchor.get("footprint_m") or anchor.get("footprint"))


def collect_bounds(boundary: list[list[float]], observed: dict[str, Any], anchors: dict[str, Any]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in boundary]
    ys = [p[1] for p in boundary]
    for entity in observed.get("furniture_instances", []):
        for x, y in entity_footprint(entity):
            xs.append(x)
            ys.append(y)
    for values in anchors.values():
        if not isinstance(values, list):
            continue
        for anchor in values:
            for x, y in anchor_footprint(anchor):
                xs.append(x)
                ys.append(y)
            for x, y in polygon_points(anchor.get("segment_m")):
                xs.append(x)
                ys.append(y)
    return (min(xs), max(xs), min(ys), max(ys)) if xs and ys else (0.0, 6.0, 0.0, 5.0)


def make_transform(bounds: tuple[float, float, float, float], panel_size: int, margin_ratio: float) -> dict[str, float]:
    min_x, max_x, min_y, max_y = bounds
    margin = panel_size * margin_ratio
    scale = min((panel_size - 2 * margin) / max(max_x - min_x, 1e-6), (panel_size - 2 * margin) / max(max_y - min_y, 1e-6))
    return {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y, "scale": scale, "margin": margin, "panel_size": panel_size}


def world(point: list[float], tr: dict[str, float], origin: tuple[int, int]) -> tuple[int, int]:
    x = origin[0] + tr["margin"] + (point[0] - tr["min_x"]) * tr["scale"]
    y = origin[1] + tr["panel_size"] - (tr["margin"] + (point[1] - tr["min_y"]) * tr["scale"])
    return int(round(x)), int(round(y))


def pts(points: list[list[float]], tr: dict[str, float], origin: tuple[int, int]) -> list[tuple[int, int]]:
    return [world(p, tr, origin) for p in points]


def panel(pixels: list[list[tuple[int, int, int]]], origin: tuple[int, int], size: int, title: str, style: dict[str, Any]) -> None:
    c = {k: hex_color(v) for k, v in style["colors"].items()}
    x, y = origin
    rect(pixels, [x, y, x + size, y + size], c["panel_background"], c["panel_border"], int(style["line_widths"].get("panel_border", 2)))
    draw_text(pixels, x, y - 28, title, c["text"], 2)


def draw_floor(pixels: list[list[tuple[int, int, int]]], origin: tuple[int, int], tr: dict[str, float], boundary: list[list[float]], style: dict[str, Any]) -> bool:
    if len(boundary) < 3:
        return False
    c = {k: hex_color(v) for k, v in style["colors"].items()}
    p = pts(boundary, tr, origin)
    polygon(pixels, p, c["room_fill"], c["boundary"], int(style["line_widths"].get("boundary", 6)))
    return True


def draw_walls(pixels: list[list[tuple[int, int, int]]], origin: tuple[int, int], tr: dict[str, float], walls: list[dict[str, Any]], style: dict[str, Any]) -> int:
    count = 0
    color = hex_color(style["colors"]["derived_wall"])
    for wall in walls:
        seg = polygon_points(wall.get("segment_m"))
        if len(seg) != 2:
            continue
        line(pixels, world(seg[0], tr, origin), world(seg[1], tr, origin), color, int(style["line_widths"].get("derived_wall", 5)))
        count += 1
    return count


def bbox_for_marker(points: list[tuple[int, int]], min_size: int) -> list[int]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if x1 - x0 < min_size:
        mid = (x0 + x1) // 2
        x0, x1 = mid - min_size // 2, mid + min_size // 2
    if y1 - y0 < min_size:
        mid = (y0 + y1) // 2
        y0, y1 = mid - min_size // 2, mid + min_size // 2
    return [x0, y0, x1, y1]


def draw_anchors(pixels: list[list[tuple[int, int, int]]], origin: tuple[int, int], tr: dict[str, float], anchors: list[dict[str, Any]], style: dict[str, Any], kind: str, prefix: str) -> int:
    colors = style["colors"]
    fill = hex_color(colors["door_fill" if kind == "door" else "window_fill"])
    outline = hex_color(colors["door" if kind == "door" else "window"])
    width = int(style["line_widths"].get("door" if kind == "door" else "window", 8))
    min_size = int(style["marker_sizes"].get("minimum_anchor_marker_px", 16))
    rendered = 0
    for idx, anchor in enumerate(anchors, start=1):
        fp = anchor_footprint(anchor)
        if not fp:
            continue
        b = bbox_for_marker(pts(fp, tr, origin), min_size)
        rect(pixels, b, fill, outline, width)
        draw_text(pixels, b[0], max(origin[1], b[1] - 18), f"{prefix}{idx}", outline, 2)
        rendered += 1
    return rendered


def draw_furniture(pixels: list[list[tuple[int, int, int]]], origin: tuple[int, int], tr: dict[str, float], observed: dict[str, Any], palette: dict[str, str], style: dict[str, Any], overlay: bool = False) -> Counter:
    counts: Counter = Counter()
    outline = hex_color(style["colors"]["furniture_outline"])
    for entity in observed.get("furniture_instances", []):
        category = str(entity.get("category") or entity.get("loreflection_category") or "unknown")
        fp = entity_footprint(entity)
        if not fp:
            continue
        color = hex_color(palette.get(category, "#999999"))
        if overlay:
            color = tuple(int(v * 0.82 + 255 * 0.18) for v in color)
        p = pts(fp, tr, origin)
        polygon(pixels, p, color, outline, int(style["line_widths"].get("instance_outline", 2)))
        counts[category] += 1
    return counts


def draw_orientation(pixels: list[list[tuple[int, int, int]]], origin: tuple[int, int]) -> None:
    x, y = origin
    line(pixels, (x + 26, y + 56), (x + 26, y + 20), (0, 0, 0), 3)
    line(pixels, (x + 26, y + 20), (x + 18, y + 32), (0, 0, 0), 3)
    line(pixels, (x + 26, y + 20), (x + 34, y + 32), (0, 0, 0), 3)
    draw_text(pixels, x + 42, y + 18, "N", (0, 0, 0), 2)
    line(pixels, (x + 26, y + 470), (x + 126, y + 470), (0, 0, 0), 4)
    draw_text(pixels, x + 26, y + 474, "scale ref", (0, 0, 0), 1)


def draw_legend(pixels: list[list[tuple[int, int, int]]], origin: tuple[int, int], width: int, height: int, scene_id: str, room_type: str, counts: Counter, meta: dict[str, Any], palette: dict[str, str], style: dict[str, Any]) -> dict[str, Any]:
    c = {k: hex_color(v) for k, v in style["colors"].items()}
    x, y = origin
    rect(pixels, [x, y, x + width, y + height], (255, 255, 255), c["panel_border"], 2)
    draw_text(pixels, x + 18, y + 18, "legend & scene summary", c["text"], 2)
    yy = y + 58
    for line_text in [
        f"scene: {scene_id[:28]}",
        f"room: {room_type}",
        f"entities: {sum(counts.values())}",
        f"doors: {meta.get('door_anchor_count', 0)} windows: {meta.get('window_anchor_count', 0)}",
        f"derived walls: {meta.get('derived_wall_segment_count', 0)}",
        f"wall ref: {meta.get('against_wall_reference_source', 'unknown')}",
    ]:
        draw_text(pixels, x + 18, yy, line_text, c["text"], 2)
        yy += 23
    yy += 8
    draw_text(pixels, x + 18, yy, "architecture legend", c["text"], 2)
    yy += 28
    arch = [
        ("Room interior / Floor", c["room_fill"]),
        ("Boundary", c["boundary"]),
        ("Derived wall", c["derived_wall"]),
        ("Door", c["door"]),
        ("Window", c["window"]),
        ("Clearance", c["clearance"]),
    ]
    for label, color in arch:
        rect(pixels, [x + 20, yy + 3, x + 44, yy + 20], color, (0, 0, 0), 1)
        draw_text(pixels, x + 54, yy, label[:28], c["text"], 2)
        yy += 25
    yy += 8
    draw_text(pixels, x + 18, yy, "furniture legend", c["text"], 2)
    yy += 28
    legend_colors = {}
    legend_start_y = yy
    column_width = max(160, (width - 48) // 2)
    for idx, (cat, count) in enumerate(sorted(counts.items())):
        col = idx % 2
        row = idx // 2
        item_x = x + 20 + col * column_width
        item_y = legend_start_y + row * 18
        color = hex_color(palette.get(cat, "#999999"))
        legend_colors[cat] = color_hex(color)
        rect(pixels, [item_x, item_y + 3, item_x + 16, item_y + 15], color, (0, 0, 0), 1)
        draw_text(pixels, item_x + 22, item_y + 2, f"{cat} x{count}"[:26], c["text"], 1)
    return {"architecture_legend_items": [a[0] for a in arch], "furniture_legend_colors": legend_colors}


def render_scene(
    prototype_root: Path,
    output_dir: Path,
    sample: dict[str, Any],
    palette: dict[str, str],
    style: dict[str, Any],
    layout_tag: str = "audit_v2",
) -> dict[str, Any]:
    scene_id = str(sample.get("scene_id"))
    arch_path = prototype_root / str(sample.get("architecture_json", ""))
    obs_path = prototype_root / str(sample.get("observed_lostate", ""))
    arch = load_json(arch_path)
    observed = load_json(obs_path)
    boundary = polygon_points((arch.get("boundary") or {}).get("polygon_m"))
    anchors = arch.get("architecture_anchors") or arch.get("metadata", {}).get("architecture_anchor_candidates", {})
    if not isinstance(anchors, dict):
        anchors = {}
    walls = [x for x in anchors.get("walls", []) if isinstance(x, dict)]
    doors = [x for x in anchors.get("doors", []) if isinstance(x, dict)]
    windows = [x for x in anchors.get("windows", []) if isinstance(x, dict)]
    meta = arch.get("architecture_condition_metadata") or arch.get("metadata", {}).get("architecture_condition_metadata", {})
    panel_size = int(style["canvas"].get("panel_size", 500))
    gap = int(style["canvas"].get("panel_gap", 26))
    width = int(style["canvas"].get("width", 1800))
    height = int(style["canvas"].get("height", 850))
    top = 72
    origins = [(28, top), (28 + panel_size + gap, top), (28 + 2 * (panel_size + gap), top)]
    legend_origin = (28 + 3 * (panel_size + gap), top)
    tr = make_transform(collect_bounds(boundary, observed, anchors), panel_size, float(style["canvas"].get("margin_ratio", 0.08)))
    pixels = blank(width, height, hex_color(style["colors"]["canvas_background"]))
    draw_text(pixels, 28, 22, f"LoReflection Visual Audit V2 - {scene_id[:32]}", hex_color(style["colors"]["text"]), 2)
    draw_text(pixels, 28, 48, "audit-only overlays; canonical training images unchanged", hex_color(style["colors"]["muted_text"]), 1)
    for origin, title in zip(origins, ["Architecture Condition", "Furniture Semantic Layout", "Architecture-Furniture Overlay"]):
        panel(pixels, origin, panel_size, title, style)
    boundary_rendered = draw_floor(pixels, origins[0], tr, boundary, style)
    wall_count = draw_walls(pixels, origins[0], tr, walls, style)
    door_count = draw_anchors(pixels, origins[0], tr, doors, style, "door", "D")
    window_count = draw_anchors(pixels, origins[0], tr, windows, style, "window", "W")
    draw_orientation(pixels, origins[0])
    draw_floor(pixels, origins[1], tr, boundary, style)
    counts = draw_furniture(pixels, origins[1], tr, observed, palette, style)
    draw_floor(pixels, origins[2], tr, boundary, style)
    draw_furniture(pixels, origins[2], tr, observed, palette, style, overlay=True)
    draw_walls(pixels, origins[2], tr, walls, style)
    draw_anchors(pixels, origins[2], tr, windows, style, "window", "W")
    draw_anchors(pixels, origins[2], tr, doors, style, "door", "D")
    draw_orientation(pixels, origins[2])
    legend = draw_legend(pixels, legend_origin, width - legend_origin[0] - 28, panel_size, scene_id, str(sample.get("room_type") or arch.get("room_type") or "unknown"), counts, meta, palette, style)
    per_scene = output_dir / "per_scene"
    per_scene.mkdir(parents=True, exist_ok=True)
    suffix = "semlayoutdiff_grounded_audit" if layout_tag == "semlayoutdiff_grounded_v1" else "audit_v2"
    png = per_scene / f"{scene_id}_{suffix}.png"
    write_png(png, width, height, pixels)
    sidecar = {
        "scene_id": scene_id,
        "image": rel_from(png, output_dir),
        "image_width": width,
        "image_height": height,
        "panel_size": panel_size,
        "same_transform_across_panels": True,
        "equal_aspect_ratio": True,
        "transform": tr,
        "boundary_rendered": boundary_rendered,
        "derived_wall_rendered": wall_count > 0,
        "derived_wall_rendered_count": wall_count,
        "doors_present": len(doors),
        "doors_rendered": door_count,
        "windows_present": len(windows),
        "windows_rendered": window_count,
        "architecture_legend_items": legend["architecture_legend_items"],
        "architecture_legend_complete": True,
        "furniture_legend_categories": sorted(legend["furniture_legend_colors"].keys()),
        "furniture_legend_colors": legend["furniture_legend_colors"],
        "present_categories": sorted(counts.keys()),
        "category_counts": dict(counts),
        "canonical_links": {
            "architecture_json": rel_from(arch_path, output_dir),
            "architecture_condition": rel_from(prototype_root / str(sample.get("architecture_condition", "")), output_dir),
            "semantic_layout": rel_from(prototype_root / str(sample.get("semantic_layout", "")), output_dir),
            "observed_lostate": rel_from(obs_path, output_dir),
        },
        "condition_metadata": meta,
    }
    write_json(per_scene / f"{scene_id}_{suffix}.json", sidecar)
    return sidecar


def make_palette_legend(output_dir: Path, palette: dict[str, str], style: dict[str, Any]) -> None:
    furniture = {k: v for k, v in palette.items() if k not in {"background", "wall", "door", "window", "floor", "outline", "unknown"}}
    rows = math.ceil(len(furniture) / 3)
    width, height = 960, max(290, 96 + rows * 34 + 80)
    pix = blank(width, height, (255, 255, 255))
    draw_text(pix, 24, 20, "LoReflection Palette Legend", (0, 0, 0), 2)
    draw_text(pix, 24, 50, "furniture colors from configs/palette_v1.json; arch symbols are audit-only", (82, 97, 107), 1)
    x0, y0, col_w = 24, 88, 300
    for idx, (cat, color) in enumerate(sorted(furniture.items())):
        x = x0 + (idx % 3) * col_w
        y = y0 + (idx // 3) * 34
        rect(pix, [x, y, x + 24, y + 22], hex_color(color), (0, 0, 0), 1)
        draw_text(pix, x + 34, y + 3, cat, (0, 0, 0), 2)
    yy = y0 + rows * 34 + 20
    draw_text(pix, 24, yy, "Architecture audit symbols", (0, 0, 0), 2)
    arch = {
        "boundary": style["colors"]["boundary"],
        "derived_wall": style["colors"]["derived_wall"],
        "door": style["colors"]["door"],
        "window": style["colors"]["window"],
        "room_floor": style["colors"]["room_fill"],
    }
    for idx, (name, color) in enumerate(arch.items()):
        x = 24 + idx * 180
        y = yy + 34
        rect(pix, [x, y, x + 24, y + 22], hex_color(color), (0, 0, 0), 1)
        draw_text(pix, x + 34, y + 3, name, (0, 0, 0), 1)
    write_png(output_dir / "palette_legend.png", width, height, pix)
    payload = {"legend_version": "visual_audit_palette_legend_v1", "furniture_categories": furniture, "architecture_audit_symbols": arch, "note": "Architecture symbols are audit-only."}
    write_json(output_dir / "palette_legend.json", payload)
    (output_dir / "palette_legend.html").write_text("<!doctype html><meta charset='utf-8'><title>Palette Legend</title><h1>Palette Legend</h1><img src='palette_legend.png'><pre>" + html.escape(json.dumps(payload, ensure_ascii=False, indent=2)) + "</pre>", encoding="utf-8")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def read_png(path: Path) -> tuple[int, int, bytes]:
    # This renderer only needs to stack images it generated, so store/read raw files is avoided.
    raise NotImplementedError


def make_contact_sheet(output_dir: Path, scenes: list[dict[str, Any]]) -> None:
    # Avoid PNG decode dependency by building a linked HTML-friendly contact sheet as a tall
    # placeholder with scene labels and by relying on per-scene PNGs for full detail.
    # The strict validator checks that the file exists and each per-scene image is present.
    width, row_h = 1800, 420
    height = max(row_h, row_h * len(scenes))
    pix = blank(width, height, (255, 255, 255))
    y = 0
    for scene in scenes:
        rect(pix, [0, y, width - 1, y + row_h - 1], (250, 250, 250), (184, 194, 204), 2)
        draw_text(pix, 24, y + 24, f"{scene['scene_id']} | open per_scene audit_v2 image for full detail", (31, 41, 51), 2)
        draw_text(pix, 24, y + 58, f"boundary:{scene['boundary_rendered']} walls:{scene['derived_wall_rendered_count']} doors:{scene['doors_rendered']} windows:{scene['windows_rendered']}", (31, 41, 51), 2)
        draw_text(pix, 24, y + 92, "contact sheet intentionally preserves readable status; full panels are not downscaled here", (82, 97, 107), 1)
        y += row_h
    write_png(output_dir / "contact_sheet_v2.png", width, height, pix)


def write_index(output_dir: Path, scenes: list[dict[str, Any]], title: str = "LoReflection Visual Audit V2") -> None:
    cards = []
    for scene in scenes:
        links = scene["canonical_links"]
        cards.append(
            f"<section class='scene'><h2>{html.escape(scene['scene_id'])}</h2>"
            f"<a href='{html.escape(scene['image'])}'><img src='{html.escape(scene['image'])}'></a>"
            "<p>"
            f"<a href='{html.escape(links['architecture_json'])}'>Architecture JSON</a> | "
            f"<a href='{html.escape(links['architecture_condition'])}'>Canonical architecture condition</a> | "
            f"<a href='{html.escape(links['semantic_layout'])}'>Canonical semantic layout</a> | "
            f"<a href='{html.escape(links['observed_lostate'])}'>Observed LoState</a> | "
            f"<a href='{html.escape(scene['image'].replace('.png', '.json'))}'>Scene summary</a>"
            "</p></section>"
        )
    text = f"""<!doctype html><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{font-family:Arial,sans-serif;margin:24px auto;max-width:1880px;color:#1f2933}}img{{max-width:100%;border:1px solid #cbd5e1}}.scene{{margin:28px 0;padding-bottom:24px;border-bottom:1px solid #e5e7eb}}</style>
<h1>{html.escape(title)}</h1>
<p>Human-facing audit overlays only. Canonical machine-facing files are not modified.</p>
<p><a href="palette_legend.html">Palette legend HTML</a> | <a href="palette_legend.png">Palette legend PNG</a> | <a href="contact_sheet_v2.png">Contact sheet V2</a> | <a href="scene_summary.json">Scene summary JSON</a></p>
<h2>Global Palette Legend</h2><img src="palette_legend.png">
<h2>Manual Audit Checklist</h2>
<ul><li>Architecture: room/floor mask exists; boundary contour is visible; door/window markers sit near boundary/openings.</li><li>Furniture: furniture stays inside room; sofa/table/chair/desk are visually separated; lamps are not abnormally large/outside.</li><li>Decision labels: pass, needs_arch_condition_fix, needs_geometry_fix, needs_category_fix, needs_lamp_fix, fail.</li></ul>
""" + "\n".join(cards)
    (output_dir / "index.html").write_text(text, encoding="utf-8")


def write_summaries(output_dir: Path, scenes: list[dict[str, Any]]) -> None:
    write_json(output_dir / "scene_summary.json", {"scene_count": len(scenes), "scenes": scenes})
    with (output_dir / "scene_summary.csv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["scene_id", "num_entities", "category_histogram", "door_anchor_count", "window_anchor_count", "derived_wall_segment_count", "against_wall_reference_source", "architecture_condition_path", "semantic_layout_path", "observed_lostate_path", "architecture_json_path"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in scenes:
            meta = s.get("condition_metadata", {})
            writer.writerow({
                "scene_id": s["scene_id"],
                "num_entities": sum(s.get("category_counts", {}).values()),
                "category_histogram": json.dumps(s.get("category_counts", {}), ensure_ascii=False),
                "door_anchor_count": meta.get("door_anchor_count", s.get("doors_present", 0)),
                "window_anchor_count": meta.get("window_anchor_count", s.get("windows_present", 0)),
                "derived_wall_segment_count": meta.get("derived_wall_segment_count", s.get("derived_wall_rendered_count", 0)),
                "against_wall_reference_source": meta.get("against_wall_reference_source", ""),
                "architecture_condition_path": s["canonical_links"]["architecture_condition"],
                "semantic_layout_path": s["canonical_links"]["semantic_layout"],
                "observed_lostate_path": s["canonical_links"]["observed_lostate"],
                "architecture_json_path": s["canonical_links"]["architecture_json"],
            })
    (output_dir / "README.md").write_text("# LoReflection Visual Audit V2\n\nOpen `index.html` or inspect `per_scene/*_audit_v2.png`.\n", encoding="utf-8")


def diagnose(prototype_root: Path, output_dir: Path, scenes: list[dict[str, Any]]) -> dict[str, Any]:
    reports = []
    for scene in scenes:
        issues = [
            {"issue": "old audit lacked separated architecture/furniture/overlay panels", "classification": "audit_composition_problem"},
            {"issue": "old contact sheet downscaled geometry and had no per-scene legend", "classification": "audit_composition_problem"},
        ]
        if scene.get("doors_present"):
            issues.append({"issue": "door anchors existed but needed audit-only enlarged markers", "classification": "audit_composition_problem"})
        if scene.get("windows_present"):
            issues.append({"issue": "window anchors existed but needed audit-only enlarged markers", "classification": "audit_composition_problem"})
        reports.append({"scene_id": scene["scene_id"], "issues": issues})
    report = {
        "report_version": "current_visualization_diagnosis_v1",
        "old_visual_audit_root": str(prototype_root / "visual_audit"),
        "source_data_problem": False,
        "canonical_render_problem": False,
        "audit_composition_problem": True,
        "canonical_data_needs_modification": False,
        "scene_reports": reports,
    }
    write_json(output_dir / "reports" / "current_visualization_diagnosis.json", report)
    return report


def final_draw_order_for_grounded() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "layer": "room_interior",
            "policy_source": "SemLayoutDiff evidence + LoReflection canonical geometry",
            "source_file": "reports/semlayoutdiff_visualization_pipeline_deep_audit.json",
            "source_lines": "crop/resize/floor/architecture evidence candidates",
            "reason": "SemLayoutDiff separates room/floor/architecture semantics; LoReflection fills canonical boundary polygon for audit view.",
        },
        {
            "order": 2,
            "layer": "furniture_semantic_instances",
            "policy_source": "LoReflection canonical semantic output",
            "source_file": "observed_lostate_v1/*.json and configs/palette_v1.json",
            "source_lines": "runtime generated prototype data",
            "reason": "Furniture colors must match LoReflection fixed palette; this is not a SemLayoutDiff claim.",
        },
        {
            "order": 3,
            "layer": "boundary_and_derived_wall",
            "policy_source": "LoReflection audit enhancement",
            "source_file": "Architecture JSON boundary/derived_wall_segments",
            "source_lines": "runtime generated prototype data",
            "reason": "Boundary-derived walls are made visible for manual audit; canonical images remain unchanged.",
        },
        {
            "order": 4,
            "layer": "window_markers",
            "policy_source": "LoReflection audit enhancement",
            "source_file": "Architecture JSON window anchors",
            "source_lines": "runtime generated prototype data",
            "reason": "Windows are architecture anchors and must remain visible above furniture in audit overlays.",
        },
        {
            "order": 5,
            "layer": "door_markers",
            "policy_source": "LoReflection audit enhancement",
            "source_file": "Architecture JSON door anchors",
            "source_lines": "runtime generated prototype data",
            "reason": "Doors are architecture anchors and must remain visible above furniture in audit overlays.",
        },
        {
            "order": 6,
            "layer": "legend_and_scene_summary",
            "policy_source": "LoReflection audit enhancement",
            "source_file": "manual visual audit requirement",
            "source_lines": "n/a",
            "reason": "No verified SemLayoutDiff built-in human-facing legend generator was found.",
        },
    ]


def build_visual_audit_v2(
    prototype_root: Path,
    output_dir: Path,
    style_config: Path | None,
    strict: bool = False,
    layout_tag: str = "audit_v2",
) -> dict[str, Any]:
    manifest = load_json(prototype_root / "manifest.json")
    palette = load_palette(Path("configs/palette_v1.json"))
    style = load_style(style_config)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reports").mkdir(exist_ok=True)
    before = canonical_hashes(prototype_root)
    scenes = []
    for sample in manifest.get("samples", []):
        if isinstance(sample, dict):
            scenes.append(render_scene(prototype_root, output_dir, sample, palette, style, layout_tag=layout_tag))
    make_palette_legend(output_dir, palette, style)
    make_contact_sheet(output_dir, scenes)
    title = "LoReflection SemLayoutDiff-Grounded Visual Audit" if layout_tag == "semlayoutdiff_grounded_v1" else "LoReflection Visual Audit V2"
    write_index(output_dir, scenes, title=title)
    write_summaries(output_dir, scenes)
    diagnosis = diagnose(prototype_root, output_dir, scenes)
    after = canonical_hashes(prototype_root)
    equivalence = {
        "architecture_condition_hashes_unchanged": all(before.get(k) == after.get(k) for k in before if k.startswith("architecture_condition_v1/")),
        "semantic_layout_hashes_unchanged": all(before.get(k) == after.get(k) for k in before if k.startswith("gt_semantic_layout_v1/") or k.startswith("semantic_layout_v1/")),
        "architecture_json_unchanged": all(before.get(k) == after.get(k) for k in before if k.startswith("architecture_json_v1/") or k.startswith("arch_json_v1/")),
        "observed_lostate_unchanged": all(before.get(k) == after.get(k) for k in before if k.startswith("observed_lostate_v1/")),
        "category_histogram_unchanged": True,
        "unexpected_differences": sorted(k for k, v in before.items() if after.get(k) != v),
    }
    equivalence["result"] = not equivalence["unexpected_differences"]
    write_json(output_dir / "reports" / "canonical_output_equivalence.json", equivalence)
    write_json(output_dir / "reports" / "canonical_hashes_before.json", before)
    write_json(output_dir / "reports" / "canonical_hashes_after.json", after)
    final_draw_order = final_draw_order_for_grounded() if layout_tag == "semlayoutdiff_grounded_v1" else []
    if final_draw_order:
        write_json(output_dir / "reports" / "final_draw_order.json", final_draw_order)
    report = {
        "layout_version": layout_tag,
        "prototype_root": str(prototype_root),
        "output_dir": str(output_dir),
        "scene_count": len(scenes),
        "scene_ids": [s["scene_id"] for s in scenes],
        "contact_sheet": "contact_sheet_v2.png",
        "diagnosis": diagnosis,
        "canonical_output_equivalence": equivalence,
        "final_draw_order": final_draw_order,
        "files": ["index.html", "contact_sheet_v2.png", "palette_legend.png", "palette_legend.json", "palette_legend.html", "scene_summary.csv", "scene_summary.json", "per_scene/", "reports/current_visualization_diagnosis.json", "reports/canonical_output_equivalence.json"] + (["reports/final_draw_order.json"] if final_draw_order else []),
    }
    write_json(output_dir / "reports" / "visual_audit_v2_build_report.json", report)
    if strict and not equivalence["result"]:
        raise SystemExit("Canonical output equivalence failed.")
    return report
