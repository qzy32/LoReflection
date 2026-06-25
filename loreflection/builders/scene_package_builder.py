#!/usr/bin/env python
"""Build a bounded real-data val50 prototype package.

This script samples a small number of 3D-FRONT scene JSON files and converts
them into LoReflection prototype artifacts. It is intentionally conservative:
it does not run Blender, model inference, training, or full dataset conversion.
Geometry that cannot be read reliably is marked with warnings and fallback
values instead of being presented as ground truth.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from loreflection.config.paths import load_authoritative_3dfront_paths


PALETTE_PATH = Path("configs/palette_v1.json")
CATEGORY_MAPPING_PATH = Path("configs/category_mapping_3dfuture_to_palette_v1.json")
PREFERRED_ROOM_TYPES = ("bedroom", "livingroom", "living room", "diningroom", "dining room")
ABSOLUTE_PATH_MARKERS = ("C:/", "C:\\", "/Users/", "/home/", "/mnt/")
CANONICAL_ACTIONS = {"keep_furniture", "keep_architecture_anchor", "keep_architecture_region", "skip"}
LEGACY_ACTION_MAP = {
    "keep_core": "keep_furniture",
    "keep_lamp": "keep_furniture",
    "architecture_anchor": "keep_architecture_anchor",
    "architecture_region": "keep_architecture_region",
    "skip_accessory": "skip",
    "skip_unknown": "skip",
}
LEGACY_GROUP_MAP = {
    "keep_core": "core_furniture",
    "keep_lamp": "lighting",
    "architecture_anchor": "architecture",
    "architecture_region": "architecture",
    "skip_accessory": "accessory",
    "skip_unknown": "unknown",
}
LEGACY_SKIP_REASON_MAP = {
    "skip_accessory": "accessory_excluded_from_v1",
    "skip_unknown": "unknown_or_unstable_mapping",
}


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"Missing env file: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def write_png(path: Path, width: int, height: int, pixels: list[list[tuple[int, int, int]]]) -> None:
    """Write an RGB PNG without third-party imaging dependencies."""
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


def blank_image(width: int, height: int, color: tuple[int, int, int]) -> list[list[tuple[int, int, int]]]:
    return [[color for _ in range(width)] for _ in range(height)]


def draw_rect(
    pixels: list[list[tuple[int, int, int]]],
    bbox: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
) -> None:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    x0, y0, x1, y1 = bbox
    x0 = max(0, min(width - 1, int(round(x0))))
    x1 = max(0, min(width - 1, int(round(x1))))
    y0 = max(0, min(height - 1, int(round(y0))))
    y1 = max(0, min(height - 1, int(round(y1))))
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    for y in range(y0, y1 + 1):
        row = pixels[y]
        for x in range(x0, x1 + 1):
            row[x] = fill
    if outline:
        for x in range(x0, x1 + 1):
            pixels[y0][x] = outline
            pixels[y1][x] = outline
        for y in range(y0, y1 + 1):
            pixels[y][x0] = outline
            pixels[y][x1] = outline


def draw_line(
    pixels: list[list[tuple[int, int, int]]],
    p0: tuple[int, int],
    p1: tuple[int, int],
    color: tuple[int, int, int],
    thickness: int = 1,
) -> None:
    """Draw a simple Bresenham line with optional square thickness."""
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    x0, y0 = p0
    x1, y1 = p1
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    radius = max(0, thickness // 2)
    while True:
        for yy in range(y0 - radius, y0 + radius + 1):
            for xx in range(x0 - radius, x0 + radius + 1):
                if 0 <= xx < width and 0 <= yy < height:
                    pixels[yy][xx] = color
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def paste(src: list[list[tuple[int, int, int]]], dst: list[list[tuple[int, int, int]]], xoff: int, yoff: int) -> None:
    for y, row in enumerate(src):
        yy = y + yoff
        if yy < 0 or yy >= len(dst):
            continue
        for x, color in enumerate(row):
            xx = x + xoff
            if 0 <= xx < len(dst[yy]):
                dst[yy][xx] = color


def load_palette() -> dict[str, tuple[int, int, int]]:
    payload = load_json(PALETTE_PATH)
    colors = payload.get("colors", {})
    palette = {key: hex_to_rgb(value) for key, value in colors.items()}
    palette.setdefault("unknown", (150, 150, 150))
    palette.setdefault("outline", (35, 35, 35))
    palette.setdefault("floor", (244, 241, 232))
    return palette


def load_category_mapping() -> dict[str, Any]:
    if CATEGORY_MAPPING_PATH.exists():
        return load_json(CATEGORY_MAPPING_PATH)
    return {"rules": []}


def normalize_text(value: Any) -> str:
    return str(value or "").lower().replace("_", " ").replace("-", " ")


def normalize_category_rule(rule: dict[str, Any]) -> dict[str, Any]:
    out = dict(rule)
    raw_action = out.get("action")
    if not raw_action:
        raise ValueError(f"Category mapping rule is missing action: {out.get('raw_category', '<unknown>')}")
    if raw_action in LEGACY_ACTION_MAP:
        out["legacy_action"] = raw_action
        out["action"] = LEGACY_ACTION_MAP[raw_action]
        out.setdefault("semantic_group", LEGACY_GROUP_MAP[raw_action])
        if raw_action in LEGACY_SKIP_REASON_MAP:
            out.setdefault("skip_reason", LEGACY_SKIP_REASON_MAP[raw_action])
    action = out.get("action")
    if action not in CANONICAL_ACTIONS:
        raise ValueError(f"Unsupported category action: {action}")
    semantic_group = out.get("semantic_group")
    if not semantic_group:
        raise ValueError(f"Category mapping rule is missing semantic_group: {out.get('raw_category', '<unknown>')}")
    if action == "keep_furniture" and not out.get("loreflection_category"):
        raise ValueError(f"keep_furniture rule is missing loreflection_category: {out.get('raw_category', '<unknown>')}")
    if action == "skip" and semantic_group in {"accessory", "unknown"} and not out.get("skip_reason"):
        raise ValueError(f"skip rule is missing skip_reason: {out.get('raw_category', '<unknown>')}")
    return out


def map_category(raw_text_parts: list[Any], mapping: dict[str, Any]) -> dict[str, Any]:
    """Return the full mapping rule with reference/category/action fields."""
    # Match higher-confidence fields first. In 3D-FUTURE, model_info.category is
    # more reliable than noisy titles/types, so a Coffee Table should not be
    # pulled into desk just because a later fallback string contains "desk".
    for part in raw_text_parts:
        text = normalize_text(part)
        if not text:
            continue
        for rule in mapping.get("rules", []):
            for token in rule.get("match_any", []):
                if normalize_text(token) in text:
                    out = normalize_category_rule(rule)
                    out.setdefault("reference_category", "unknown")
                    out.setdefault("loreflection_category", "unknown")
                    out.setdefault("action", "skip")
                    out.setdefault("palette_alias_used", False)
                    return out
    default = normalize_category_rule(dict(mapping.get("default", {})))
    default.setdefault("reference_category", "unknown")
    default.setdefault("loreflection_category", "unknown")
    default.setdefault("action", "skip")
    default.setdefault("palette_alias_used", False)
    return default


def category_prior(category: str) -> tuple[float, float]:
    priors = {
        "bed": (2.1, 1.6),
        "wardrobe": (1.4, 0.6),
        "desk": (1.2, 0.7),
        "chair": (0.6, 0.6),
        "sofa": (2.0, 0.9),
        "table": (1.4, 0.8),
        "cabinet": (1.2, 0.5),
        "tv_stand": (1.4, 0.45),
        "bookshelf": (1.0, 0.35),
        "nightstand": (0.55, 0.45),
        "pendant_lamp": (0.45, 0.45),
        "ceiling_lamp": (0.55, 0.55),
        "lamp": (0.45, 0.45),
        "unknown": (0.8, 0.6),
    }
    return priors.get(category, priors["unknown"])


def index_model_info(future_root: Path, max_raw_examples: int = 0, model_info_path: Path | None = None) -> dict[str, Any]:
    model_info = model_info_path or (future_root / "model_info.json")
    if not model_info.exists():
        raise FileNotFoundError(f"Missing 3D-FUTURE model_info.json: {model_info}")
    data = load_json(model_info)
    if isinstance(data, dict):
        entries = list(data.values())
    elif isinstance(data, list):
        entries = data
    else:
        entries = []
    by_model_id: dict[str, dict[str, Any]] = {}
    category_fields = set()
    for item in entries:
        if not isinstance(item, dict):
            continue
        model_id = item.get("model_id") or item.get("jid") or item.get("id") or item.get("uid")
        if not model_id:
            continue
        category = item.get("category") or item.get("super-category") or item.get("super_category") or item.get("name")
        for key in ("category", "super-category", "super_category", "name"):
            if key in item:
                category_fields.add(key)
        by_model_id[str(model_id)] = {
            "category": category or "unknown",
            "super_category": item.get("super-category") or item.get("super_category") or "",
            "raw": item if max_raw_examples else {},
        }
    return {
        "index_version": "model_info_index_v1",
        "source": model_info.as_posix(),
        "num_models": len(by_model_id),
        "category_fields": sorted(category_fields),
        "by_model_id": by_model_id,
    }


def get_scene_id(scene_path: Path, scene: dict[str, Any]) -> str:
    return str(scene.get("uid") or scene.get("scene_id") or scene_path.stem).replace("/", "_")


def collect_room_type(value: Any) -> str | None:
    candidates: list[str] = []

    def scan(node: Any, depth: int = 0) -> None:
        if depth > 5 or len(candidates) >= 10:
            return
        if isinstance(node, dict):
            for key in ("roomType", "room_type", "type", "contentType", "category"):
                raw = node.get(key)
                if isinstance(raw, str):
                    lower = raw.lower()
                    if "room" in lower or lower in PREFERRED_ROOM_TYPES or "bed" in lower or "dining" in lower or "living" in lower:
                        candidates.append(lower)
            for child in node.values():
                scan(child, depth + 1)
        elif isinstance(node, list):
            for child in node[:20]:
                scan(child, depth + 1)

    scan(value)
    for preferred in PREFERRED_ROOM_TYPES:
        for item in candidates:
            if preferred in item:
                return preferred.replace(" ", "")
    return candidates[0].replace(" ", "") if candidates else None


def find_furniture_list(scene: dict[str, Any]) -> list[dict[str, Any]]:
    furniture = scene.get("furniture", [])
    if isinstance(furniture, list):
        return [x for x in furniture if isinstance(x, dict)]
    return []


def iter_room_children(scene: dict[str, Any]) -> list[dict[str, Any]]:
    scene_obj = scene.get("scene", {})
    rooms = []
    if isinstance(scene_obj, dict):
        raw_rooms = scene_obj.get("room") or scene_obj.get("rooms") or []
        if isinstance(raw_rooms, list):
            rooms = raw_rooms
    children: list[dict[str, Any]] = []
    for room_index, room in enumerate(rooms):
        if not isinstance(room, dict):
            continue
        for child_index, child in enumerate(room.get("children", []) if isinstance(room.get("children"), list) else []):
            if not isinstance(child, dict):
                continue
            item = dict(child)
            item["_room_index"] = room_index
            item["_child_index"] = child_index
            item["_source_path"] = f"scene.room[{room_index}].children[{child_index}]"
            children.append(item)
    return children


def collect_transform_index(scene: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """Index transform-bearing room children by several safe link rules."""
    index: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for child in iter_room_children(scene):
        has_transform = any(k in child for k in ("pos", "position", "rot", "rotation", "scale"))
        if not has_transform:
            continue
        values = {
            "child.ref": child.get("ref"),
            "child.uid": child.get("uid"),
            "child.instanceid": child.get("instanceid") or child.get("instanceId"),
            "child.jid": child.get("jid"),
        }
        for source, value in values.items():
            if value is not None:
                index[source].setdefault(str(value), child)
    return index


def find_transform_for_furniture(
    furniture: dict[str, Any],
    transform_index: dict[str, dict[str, dict[str, Any]]],
) -> tuple[dict[str, Any] | None, str]:
    uid = str(furniture.get("uid") or furniture.get("id") or "")
    jid = str(furniture.get("jid") or furniture.get("model_id") or "")
    rules = [
        ("child.ref -> furniture.uid", "child.ref", uid),
        ("child.uid -> furniture.uid", "child.uid", uid),
        ("child.instanceid -> furniture.uid", "child.instanceid", uid),
        ("child.jid -> furniture.jid", "child.jid", jid),
        ("child.ref -> furniture.jid", "child.ref", jid),
    ]
    for source, index_key, value in rules:
        if value and value in transform_index.get(index_key, {}):
            return transform_index[index_key][value], source
    return None, "missing"


def vec3(value: Any) -> tuple[float, float, float] | None:
    if isinstance(value, list) and len(value) >= 3:
        try:
            return float(value[0]), float(value[1]), float(value[2])
        except (TypeError, ValueError):
            return None
    if isinstance(value, dict):
        try:
            return float(value.get("x", 0)), float(value.get("y", 0)), float(value.get("z", 0))
        except (TypeError, ValueError):
            return None
    return None


def yaw_from_rotation(value: Any) -> float:
    if isinstance(value, list) and value:
        try:
            if len(value) >= 4:
                # 3D-FRONT quaternions are commonly [x, y, z, w]; top-down yaw is around Y.
                return 2.0 * math.atan2(float(value[1]), float(value[3]))
            return float(value[-1])
        except (TypeError, ValueError):
            return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def extract_entity(
    furniture: dict[str, Any],
    transform: dict[str, Any] | None,
    transform_source: str,
    model_index: dict[str, Any],
    category_mapping: dict[str, Any],
    fallback_index: int,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    uid = str(furniture.get("uid") or furniture.get("id") or f"furniture_{fallback_index:03d}")
    jid = str(furniture.get("jid") or furniture.get("model_id") or "")
    model_meta = model_index["by_model_id"].get(jid, {}) if jid else {}
    raw_category = model_meta.get("category") or furniture.get("category") or ""
    raw_super_category = model_meta.get("super_category") or ""
    raw_title = furniture.get("title") or model_meta.get("name") or ""
    category_rule = map_category([raw_category, raw_super_category, raw_title, furniture.get("type")], category_mapping)
    reference_category = category_rule.get("reference_category", "unknown")
    category = category_rule.get("loreflection_category", "unknown")
    mapping_action = category_rule.get("action", "skip")
    semantic_group = category_rule.get("semantic_group", "unknown")
    mapping_status = "matched" if jid and jid in model_index["by_model_id"] else "unmatched" if jid else "fallback"
    if mapping_status != "matched":
        warnings.append(f"{uid}: jid mapping status is {mapping_status}.")

    center: tuple[float, float]
    orientation = 0.0
    if transform:
        pos = vec3(transform.get("pos") or transform.get("position") or transform.get("translate"))
        if pos:
            center = (pos[0], pos[2])
        else:
            center = (float(fallback_index % 4) * 1.2, float(fallback_index // 4) * 1.0)
            warnings.append(f"{uid}: missing transform position; used grid fallback.")
        orientation = yaw_from_rotation(transform.get("rot") or transform.get("rotation"))
        scale = vec3(transform.get("scale"))
    else:
        center = (float(fallback_index % 4) * 1.2, float(fallback_index // 4) * 1.0)
        scale = None
        warnings.append(f"{uid}: missing transform node; used grid fallback.")

    prior_w, prior_h = category_prior(category)
    raw_size = vec3(furniture.get("size"))
    raw_bbox = furniture.get("bbox")
    if raw_size:
        width = max(0.2, abs(raw_size[0]))
        height = max(0.2, abs(raw_size[2]))
        size_source = "furniture.size"
    elif isinstance(raw_bbox, list) and len(raw_bbox) >= 6:
        try:
            width = max(0.2, abs(float(raw_bbox[3]) - float(raw_bbox[0])))
            height = max(0.2, abs(float(raw_bbox[5]) - float(raw_bbox[2])))
            size_source = "furniture.bbox"
        except (TypeError, ValueError):
            width, height = prior_w, prior_h
            size_source = "category_prior"
            warnings.append(f"{uid}: invalid bbox size; used category prior fallback.")
    elif scale:
        width = max(0.2, abs(scale[0]) * prior_w)
        height = max(0.2, abs(scale[2]) * prior_h)
        size_source = "transform.scale_x_category_prior"
    else:
        width, height = prior_w, prior_h
        size_source = "category_prior"
        warnings.append(f"{uid}: size from category prior fallback.")

    footprint = [
        [center[0] - width / 2, center[1] - height / 2],
        [center[0] + width / 2, center[1] - height / 2],
        [center[0] + width / 2, center[1] + height / 2],
        [center[0] - width / 2, center[1] + height / 2],
    ]
    return {
        "instance_id": uid,
        "category": category,
        "raw_category": raw_category,
        "raw_super_category": raw_super_category,
        "raw_title": raw_title,
        "reference_category": reference_category,
        "loreflection_category": category,
        "mapping_action": mapping_action,
        "semantic_group": semantic_group,
        "skip_reason": category_rule.get("skip_reason", ""),
        "legacy_action": category_rule.get("legacy_action", ""),
        "mapping_reason": category_rule.get("reason", ""),
        "anchor_type": category_rule.get("anchor_type", ""),
        "palette_alias_used": bool(category_rule.get("palette_alias_used", False)),
        "palette_alias_reason": category_rule.get("alias_reason", ""),
        "is_lamp": semantic_group == "lighting",
        "source_jid": jid,
        "center_m": [center[0], center[1]],
        "size_m": [width, height],
        "size_source": size_source,
        "orientation": orientation,
        "footprint_m": footprint,
        "mapping_status": mapping_status,
        "transform_source": transform_source,
    }, warnings


def rectangle_from_extents(min_x: float, max_x: float, min_y: float, max_y: float) -> list[list[float]]:
    return [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]


def try_floor_mesh_boundary(scene: dict[str, Any]) -> tuple[list[list[float]] | None, list[str]]:
    warnings: list[str] = []
    mesh_list = scene.get("mesh")
    if not isinstance(mesh_list, list):
        return None, warnings
    xs: list[float] = []
    zs: list[float] = []
    for mesh in mesh_list:
        if not isinstance(mesh, dict):
            continue
        text = " ".join(str(mesh.get(k, "")) for k in ("type", "uid", "jid", "material", "constructid")).lower()
        is_floor_like = "floor" in text or "ground" in text or "bottom" in text
        if not is_floor_like:
            continue
        xyz = mesh.get("xyz")
        if not isinstance(xyz, list):
            continue
        coords = xyz
        if coords and isinstance(coords[0], list):
            points = coords
        else:
            points = [coords[i : i + 3] for i in range(0, len(coords), 3)]
        for point in points:
            if isinstance(point, list) and len(point) >= 3:
                try:
                    xs.append(float(point[0]))
                    zs.append(float(point[2]))
                except (TypeError, ValueError):
                    continue
    if len(xs) >= 3 and len(zs) >= 3:
        return rectangle_from_extents(min(xs), max(xs), min(zs), max(zs)), warnings
    return None, warnings


def try_room_bbox_boundary(scene: dict[str, Any]) -> tuple[list[list[float]] | None, list[str]]:
    scene_obj = scene.get("scene", {})
    rooms = scene_obj.get("room") or scene_obj.get("rooms") if isinstance(scene_obj, dict) else []
    if not isinstance(rooms, list):
        return None, []
    xs: list[float] = []
    zs: list[float] = []
    for room in rooms:
        if not isinstance(room, dict) or room.get("empty") is True:
            continue
        pos = vec3(room.get("pos") or room.get("position")) or (0.0, 0.0, 0.0)
        size = vec3(room.get("size") or room.get("scale"))
        if not size:
            continue
        width = abs(size[0])
        depth = abs(size[2])
        if width <= 0 or depth <= 0:
            continue
        xs.extend([pos[0] - width / 2, pos[0] + width / 2])
        zs.extend([pos[2] - depth / 2, pos[2] + depth / 2])
    if xs and zs:
        return rectangle_from_extents(min(xs), max(xs), min(zs), max(zs)), []
    return None, []


def compute_boundary(scene: dict[str, Any], entities: list[dict[str, Any]]) -> tuple[list[list[float]], str, list[str]]:
    floor_boundary, floor_warnings = try_floor_mesh_boundary(scene)
    if floor_boundary:
        return floor_boundary, "floor_mesh", floor_warnings
    room_boundary, room_warnings = try_room_bbox_boundary(scene)
    if room_boundary:
        return room_boundary, "room_bbox", room_warnings
    warnings = ["boundary_source = bbox_fallback"]
    if not entities:
        return [[0, 0], [6, 0], [6, 5], [0, 5]], "bbox_fallback", warnings
    xs: list[float] = []
    ys: list[float] = []
    for entity in entities:
        for x, y in entity.get("footprint_m", []):
            xs.append(float(x))
            ys.append(float(y))
    if not xs or not ys:
        return [[0, 0], [6, 0], [6, 5], [0, 5]], "bbox_fallback", warnings
    pad = 1.0
    min_x, max_x = min(xs) - pad, max(xs) + pad
    min_y, max_y = min(ys) - pad, max(ys) + pad
    if math.isclose(min_x, max_x):
        max_x += 5
    if math.isclose(min_y, max_y):
        max_y += 4
    return rectangle_from_extents(min_x, max_x, min_y, max_y), "bbox_fallback", warnings


def polygon_area(points: list[list[float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for idx, p0 in enumerate(points):
        p1 = points[(idx + 1) % len(points)]
        area += p0[0] * p1[1] - p1[0] * p0[1]
    return abs(area) * 0.5


def derive_wall_segments_from_boundary(boundary: list[list[float]]) -> list[dict[str, Any]]:
    """Derive immutable architecture wall references from a boundary polygon."""
    segments: list[dict[str, Any]] = []
    if len(boundary) < 3:
        return segments
    for idx, start in enumerate(boundary):
        end = boundary[(idx + 1) % len(boundary)]
        if start == end:
            continue
        segments.append(
            {
                "anchor_id": f"wall_derived_{idx:03d}",
                "anchor_type": "wall",
                "segment_m": [[float(start[0]), float(start[1])], [float(end[0]), float(end[1])]],
                "source": "boundary_derived",
                "boundary_edge_index": idx,
            }
        )
    return segments


def world_to_px(point: list[float], boundary: list[list[float]], image_size: int, margin: int = 24) -> tuple[int, int]:
    xs = [p[0] for p in boundary]
    ys = [p[1] for p in boundary]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    scale = min((image_size - 2 * margin) / max(max_x - min_x, 1e-6), (image_size - 2 * margin) / max(max_y - min_y, 1e-6))
    x = margin + (point[0] - min_x) * scale
    y = image_size - (margin + (point[1] - min_y) * scale)
    return int(round(x)), int(round(y))


def footprint_bbox_px(entity: dict[str, Any], boundary: list[list[float]], image_size: int) -> list[int]:
    pts = [world_to_px(point, boundary, image_size) for point in entity.get("footprint_m", [])]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)] if pts else [0, 0, 1, 1]


def render_scene_png(
    path: Path,
    entities: list[dict[str, Any]],
    boundary: list[list[float]],
    image_size: int,
    palette: dict[str, tuple[int, int, int]],
) -> list[list[tuple[int, int, int]]]:
    pixels = blank_image(image_size, image_size, palette["floor"])
    bx = [world_to_px(point, boundary, image_size) for point in boundary]
    if bx:
        xs = [p[0] for p in bx]
        ys = [p[1] for p in bx]
        draw_rect(pixels, (min(xs), min(ys), max(xs), max(ys)), palette["floor"], palette["outline"])
    for entity in entities:
        color = palette.get(entity["category"], palette["unknown"])
        bbox = footprint_bbox_px(entity, boundary, image_size)
        draw_rect(pixels, tuple(bbox), color, palette["outline"])
        entity["bbox_px"] = bbox
        entity["area_px"] = max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])
    write_png(path, image_size, image_size, pixels)
    return pixels


def render_architecture_condition_png(
    path: Path,
    boundary: list[list[float]],
    anchors: dict[str, list[dict[str, Any]]],
    derived_wall_segments: list[dict[str, Any]],
    image_size: int,
    palette: dict[str, tuple[int, int, int]],
) -> list[list[tuple[int, int, int]]]:
    pixels = blank_image(image_size, image_size, palette.get("background", (255, 255, 255)))
    bx = [world_to_px(point, boundary, image_size) for point in boundary]
    if bx:
        xs = [p[0] for p in bx]
        ys = [p[1] for p in bx]
        draw_rect(pixels, (min(xs), min(ys), max(xs), max(ys)), palette.get("floor", (244, 241, 232)), palette.get("wall", (32, 32, 32)))
        for idx, p0 in enumerate(bx):
            p1 = bx[(idx + 1) % len(bx)]
            draw_line(pixels, p0, p1, palette.get("wall", (32, 32, 32)), thickness=3)
    for segment in derived_wall_segments:
        points = segment.get("segment_m") or []
        if len(points) != 2:
            continue
        p0 = world_to_px(points[0], boundary, image_size)
        p1 = world_to_px(points[1], boundary, image_size)
        draw_line(pixels, p0, p1, palette.get("wall", (32, 32, 32)), thickness=3)
    for anchor_type, color_key in [("doors", "door"), ("windows", "window"), ("openings", "door")]:
        color = palette.get(color_key, (180, 80, 80))
        for anchor in anchors.get(anchor_type, []):
            footprint = anchor.get("footprint_m") or []
            if not footprint:
                continue
            pts = [world_to_px(point, boundary, image_size) for point in footprint]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            draw_rect(pixels, (min(xs), min(ys), max(xs), max(ys)), color, palette.get("outline", (35, 35, 35)))
    write_png(path, image_size, image_size, pixels)
    return pixels


def make_contact_sheet(images: list[list[list[tuple[int, int, int]]]], output: Path, image_size: int) -> None:
    if not images:
        return
    thumb = 160
    cols = min(3, len(images))
    rows = math.ceil(len(images) / cols)
    sheet = blank_image(cols * thumb, rows * thumb, (255, 255, 255))
    for idx, img in enumerate(images):
        scale = image_size / thumb
        small = blank_image(thumb, thumb, (255, 255, 255))
        for y in range(thumb):
            sy = min(image_size - 1, int(y * scale))
            for x in range(thumb):
                sx = min(image_size - 1, int(x * scale))
                small[y][x] = img[sy][sx]
        paste(small, sheet, (idx % cols) * thumb, (idx // cols) * thumb)
    write_png(output, cols * thumb, rows * thumb, sheet)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def has_absolute_marker(payload: Any) -> bool:
    text = json.dumps(payload, ensure_ascii=False)
    return any(marker in text for marker in ABSOLUTE_PATH_MARKERS)


def count_warning_types(field_warnings_path: Path) -> Counter:
    counts = Counter()
    if not field_warnings_path.exists():
        return counts
    payload = load_json(field_warnings_path)
    warnings = payload.get("warnings", {})
    if not isinstance(warnings, dict):
        return counts
    for items in warnings.values():
        if not isinstance(items, list):
            continue
        for item in items:
            text = str(item)
            if "missing transform node" in text:
                counts["missing_transform"] += 1
            if "size from category prior fallback" in text:
                counts["size_prior_fallback"] += 1
            if "boundary_source = bbox_fallback" in text:
                counts["bbox_fallback_boundary_warning"] += 1
            if "jid mapping status is unmatched" in text:
                counts["unmatched_jid"] += 1
    return counts


def maybe_write_comparison_report(output_root: Path, conversion_report: dict[str, Any], jid_report: dict[str, Any]) -> None:
    old_root = output_root.parent / "val50_prototype_v1"
    old_conversion_path = old_root / "reports" / "conversion_report.json"
    old_warnings_path = old_root / "reports" / "field_warnings.json"
    if not old_conversion_path.exists():
        return
    old_conversion = load_json(old_conversion_path)
    old_jid_path = old_root / str(old_conversion.get("jid_mapping_report", "category_mapping_v1/jid_mapping_report.json"))
    old_jid = load_json(old_jid_path) if old_jid_path.exists() else {}
    old_warning_counts = count_warning_types(old_warnings_path)
    new_warning_counts = count_warning_types(output_root / "reports" / "field_warnings.json")
    comparison = {
        "schema_version": "real-val50-prototype-before-after-comparison-v1",
        "old_root": old_root.as_posix(),
        "new_root": output_root.as_posix(),
        "category_mapping": {
            "old_unknown_count": old_conversion.get("semantic_layout", {}).get("unknown_category_count"),
            "new_unknown_count": conversion_report.get("semantic_layout", {}).get("unknown_category_count"),
            "old_loreflection_category_histogram": old_jid.get("category_histogram", {}),
            "new_loreflection_category_histogram": jid_report.get("category_histogram", {}),
            "new_reference_category_histogram": jid_report.get("reference_category_histogram", {}),
            "new_raw_category_histogram": jid_report.get("raw_category_histogram", {}),
            "remaining_unknown_examples": jid_report.get("unknown_raw_category_histogram", {}),
        },
        "transform_extraction": {
            "old_missing_transform": old_warning_counts.get("missing_transform", 0),
            "new_missing_transform": new_warning_counts.get("missing_transform", 0),
            "old_size_prior_fallback": old_warning_counts.get("size_prior_fallback", 0),
            "new_size_prior_fallback": new_warning_counts.get("size_prior_fallback", 0),
            "new_transform_source_summary": conversion_report.get("transform_extraction", {}).get("transform_source_summary", {}),
            "new_size_source_summary": conversion_report.get("transform_extraction", {}).get("size_source_summary", {}),
        },
        "boundary_extraction": {
            "old_boundary_source_summary": old_conversion.get("architecture", {}).get("boundary_source_summary", {}),
            "new_boundary_source_summary": conversion_report.get("architecture", {}).get("boundary_source_summary", {}),
        },
        "scale_to_50_gate": {
            "can_scale": "uncertain",
            "reason": "Run manual visual audit on contact sheet; converter no longer has all-bbox boundary if room_bbox/floor_mesh is present.",
        },
    }
    write_json(output_root / "reports" / "before_after_comparison_report.json", comparison)


def select_scenes(front_root: Path, model_index: dict[str, Any], num_scenes: int, seed: int) -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    json_files = sorted(front_root.glob("*.json"))
    rng = random.Random(seed)
    rng.shuffle(json_files)
    scored: list[tuple[int, Path, dict[str, Any], dict[str, Any]]] = []
    for path in json_files:
        try:
            scene = load_json(path)
        except Exception:
            continue
        if not isinstance(scene, dict):
            continue
        furniture = find_furniture_list(scene)
        jids = [str(item.get("jid") or "") for item in furniture]
        valid_jids = [jid for jid in jids if jid]
        matched = [jid for jid in valid_jids if jid in model_index["by_model_id"]]
        room_type = collect_room_type(scene) or "unknown"
        score = 0
        score += 4 if scene.get("uid") else 0
        score += 3 if scene.get("scene") is not None else 0
        score += 3 if isinstance(scene.get("furniture"), list) else 0
        score += min(len(valid_jids), 5)
        score += min(len(matched), 5) * 2
        score += 4 if any(preferred in room_type for preferred in PREFERRED_ROOM_TYPES) else 0
        if len(valid_jids) >= 3 and matched:
            scored.append((score, path, scene, {"room_type": room_type, "valid_jids": valid_jids, "matched_jids": matched}))
        if len(scored) >= num_scenes * 20:
            break
    scored.sort(key=lambda item: item[0], reverse=True)
    return [(path, scene, info) for _, path, scene, info in scored[:num_scenes]]


def read_scene_ids_file(path: Path) -> list[str]:
    scene_ids = [line.strip().lstrip("\ufeff") for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    duplicates = [scene_id for scene_id, count in Counter(scene_ids).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate scene ids in {path}: {duplicates}")
    return scene_ids


def select_scenes_by_id(front_root: Path, model_index: dict[str, Any], scene_ids: list[str]) -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    def build_record(path: Path) -> tuple[str, Path, dict[str, Any], dict[str, Any]] | None:
        try:
            scene = load_json(path)
        except Exception:
            return None
        if not isinstance(scene, dict):
            return None
        scene_id = get_scene_id(path, scene)
        furniture = find_furniture_list(scene)
        jids = [str(item.get("jid") or "") for item in furniture]
        valid_jids = [jid for jid in jids if jid]
        matched = [jid for jid in valid_jids if jid in model_index["by_model_id"]]
        return (
            scene_id,
            path,
            scene,
            {
                "room_type": collect_room_type(scene) or "unknown",
                "valid_jids": valid_jids,
                "matched_jids": matched,
                "selection_mode": "scene_ids_file",
            },
        )

    by_scene_id: dict[str, tuple[Path, dict[str, Any], dict[str, Any]]] = {}
    for scene_id in scene_ids:
        path = front_root / f"{scene_id}.json"
        if path.exists():
            record = build_record(path)
            if record:
                resolved_scene_id, resolved_path, scene, info = record
                by_scene_id[resolved_scene_id] = (resolved_path, scene, info)
    unresolved = [scene_id for scene_id in scene_ids if scene_id not in by_scene_id]
    if unresolved:
        for path in sorted(front_root.glob("*.json")):
            if not unresolved:
                break
            if path.stem in by_scene_id:
                continue
            record = build_record(path)
            if not record:
                continue
            resolved_scene_id, resolved_path, scene, info = record
            if resolved_scene_id in unresolved:
                by_scene_id[resolved_scene_id] = (resolved_path, scene, info)
                unresolved = [scene_id for scene_id in unresolved if scene_id != resolved_scene_id]
    missing = [scene_id for scene_id in scene_ids if scene_id not in by_scene_id]
    if missing:
        raise FileNotFoundError(f"Requested scene ids not found under {front_root}: {missing}")
    return [by_scene_id[scene_id] for scene_id in scene_ids]


def build(args: argparse.Namespace) -> dict[str, Any]:
    dataset_paths = load_authoritative_3dfront_paths(args.env_file)
    front_root = dataset_paths.scene_root
    future_root = dataset_paths.future_model_root
    texture_root = dataset_paths.texture_root or (dataset_paths.dataset_root / "3D-FRONT-texture")
    dataset_bundle = dataset_paths.dataset_root
    output_root = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    progress_log = output_root / "reports" / "native_build_progress.log"

    def mark_progress(message: str) -> None:
        progress_log.parent.mkdir(parents=True, exist_ok=True)
        with progress_log.open("a", encoding="utf-8") as f:
            f.write(message + "\n")

    dirs = {
        "source": output_root / "source_samples" / "scene_json",
        "arch": output_root / "arch_json_v1",
        "arch_condition": output_root / "architecture_condition_v1",
        "semantic": output_root / "gt_semantic_layout_v1",
        "observed": output_root / "observed_lostate_v1",
        "mapping": output_root / "category_mapping_v1",
        "preview_scene": output_root / "preview" / "per_scene",
        "reports": output_root / "reports",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    palette = load_palette()
    category_mapping = load_category_mapping()
    mark_progress("loaded_palette_and_category_mapping")
    model_index = index_model_info(future_root, model_info_path=dataset_paths.future_model_info)
    model_index_path = dirs["mapping"] / "model_info_index.json"
    write_json(model_index_path, model_index)
    mark_progress("wrote_model_info_index")

    requested_scene_ids: list[str] = []
    if getattr(args, "scene_ids_file", None):
        requested_scene_ids = read_scene_ids_file(args.scene_ids_file)
        selected = select_scenes_by_id(front_root, model_index, requested_scene_ids)
        args.num_scenes = len(requested_scene_ids)
    else:
        selected = select_scenes(front_root, model_index, args.num_scenes, args.seed)
        if args.strict and len(selected) < args.num_scenes:
            raise RuntimeError(f"Only selected {len(selected)} scenes; requested {args.num_scenes}.")
    mark_progress(f"selected_scenes={len(selected)}")

    samples = []
    all_warnings: dict[str, list[str]] = {}
    contact_images = []
    mapping_counter = Counter()
    category_histogram = Counter()
    reference_category_histogram = Counter()
    raw_category_histogram = Counter()
    unknown_raw_category_histogram = Counter()
    skipped_accessory_histogram = Counter()
    transform_source_counter = Counter()
    size_source_counter = Counter()
    action_counter = Counter()
    semantic_group_counter = Counter()
    furniture_group_counter = Counter()
    skipped_group_counter = Counter()
    skip_reason_counter = Counter()
    architecture_type_counter = Counter()
    legacy_action_counter = Counter()
    palette_alias_used_count = 0
    core_missing_transform_count = 0
    lamp_missing_transform_count = 0
    noncore_missing_transform_count = 0
    core_unknown_count = 0
    lamp_unknown_count = 0
    semantic_drawn_count = 0
    semantic_skipped_count = 0
    door_anchor_count = 0
    window_anchor_count = 0
    wall_anchor_count = 0
    derived_wall_segment_count_total = 0
    architecture_condition_boundary_contour_count = 0
    architecture_condition_floor_mask_count = 0
    against_wall_reference_sources = Counter()
    boundary_sources = Counter()
    room_type_extracted = 0
    drawable_count = 0
    skipped_count = 0
    unknown_count = 0
    entities_per_scene: dict[str, int] = {}
    lamp_entities_per_scene: dict[str, int] = {}
    total_furniture = valid_jid = matched_jid = unmatched_jid = empty_jid = 0
    matched_examples: list[str] = []
    unmatched_examples: list[str] = []

    for scene_path, scene, info in selected:
        scene_id = get_scene_id(scene_path, scene)
        mark_progress(f"scene_start:{scene_id}")
        room_type = info.get("room_type") or "unknown"
        if room_type != "unknown":
            room_type_extracted += 1
        warnings: list[str] = []
        source_copy = dirs["source"] / f"{scene_id}.json"
        shutil.copy2(scene_path, source_copy)

        furniture_list = find_furniture_list(scene)
        transform_index = collect_transform_index(scene)
        entities: list[dict[str, Any]] = []
        architecture_anchors = {"doors": [], "windows": [], "walls": [], "floor": [], "openings": []}
        for idx, furniture in enumerate(furniture_list):
            jid = str(furniture.get("jid") or "")
            total_furniture += 1
            if jid:
                valid_jid += 1
                if jid in model_index["by_model_id"]:
                    matched_jid += 1
                    if len(matched_examples) < 10:
                        matched_examples.append(jid)
                else:
                    unmatched_jid += 1
                    if len(unmatched_examples) < 10:
                        unmatched_examples.append(jid)
            else:
                empty_jid += 1

            uid = str(furniture.get("uid") or furniture.get("id") or "")
            transform, transform_source = find_transform_for_furniture(furniture, transform_index)
            entity, entity_warnings = extract_entity(furniture, transform, transform_source, model_index, category_mapping, idx)
            warnings.extend(entity_warnings)
            action = entity["mapping_action"]
            semantic_group = entity.get("semantic_group", "unknown")
            action_counter[action] += 1
            semantic_group_counter[semantic_group] += 1
            if entity.get("legacy_action"):
                legacy_action_counter[entity["legacy_action"]] += 1
            if entity.get("palette_alias_used"):
                palette_alias_used_count += 1
            reference_category_histogram[entity["reference_category"]] += 1
            raw_key = str(entity.get("raw_category") or entity.get("raw_title") or entity.get("raw_super_category") or "unknown")
            raw_category_histogram[raw_key] += 1
            if action == "skip":
                skipped_group_counter[semantic_group] += 1
                skip_reason = entity.get("skip_reason") or "unspecified"
                skip_reason_counter[skip_reason] += 1
                if semantic_group == "unknown":
                    unknown_raw_category_histogram[raw_key] += 1
                if semantic_group == "accessory":
                    skipped_accessory_histogram[raw_key] += 1
            transform_source_counter[entity["transform_source"]] += 1
            size_source_counter[entity["size_source"]] += 1
            mapping_counter[entity["mapping_status"]] += 1
            if entity["transform_source"] == "missing":
                if action == "keep_furniture" and semantic_group == "core_furniture":
                    core_missing_transform_count += 1
                elif action == "keep_furniture" and semantic_group == "lighting":
                    lamp_missing_transform_count += 1
                else:
                    noncore_missing_transform_count += 1
            if action == "keep_furniture":
                furniture_group_counter[semantic_group] += 1
                if entity["category"] == "unknown":
                    if semantic_group == "lighting":
                        lamp_unknown_count += 1
                    else:
                        core_unknown_count += 1
                category_histogram[entity["category"]] += 1
                entities.append(entity)
            elif action == "keep_architecture_anchor":
                semantic_skipped_count += 1
                architecture_type_counter["anchor"] += 1
                anchor_type = entity.get("anchor_type") or "opening"
                if anchor_type == "door":
                    architecture_anchors["doors"].append(entity)
                    door_anchor_count += 1
                elif anchor_type == "window":
                    architecture_anchors["windows"].append(entity)
                    window_anchor_count += 1
                elif anchor_type == "wall":
                    architecture_anchors["walls"].append(entity)
                    wall_anchor_count += 1
                elif anchor_type == "floor":
                    architecture_anchors["floor"].append(entity)
                else:
                    architecture_anchors["openings"].append(entity)
            elif action == "keep_architecture_region":
                semantic_skipped_count += 1
                architecture_type_counter["region"] += 1
                architecture_anchors["floor"].append(entity)
            elif action == "skip":
                semantic_skipped_count += 1
            else:
                raise ValueError(f"Unsupported category action: {action}")

        if not entities:
            skipped_count += len(furniture_list)
            warnings.append("No drawable furniture entities extracted.")
        else:
            drawable_count += len(entities)
            semantic_drawn_count += len(entities)

        boundary, boundary_source, boundary_warnings = compute_boundary(scene, entities)
        boundary_sources[boundary_source] += 1
        warnings.extend(boundary_warnings)

        derived_wall_segments = derive_wall_segments_from_boundary(boundary)
        derived_wall_segment_count_total += len(derived_wall_segments)
        raw_wall_anchor_count = len(architecture_anchors.get("walls", []))
        if raw_wall_anchor_count > 0:
            against_wall_reference_source = "explicit_wall"
        elif derived_wall_segments:
            against_wall_reference_source = "boundary_derived"
        else:
            against_wall_reference_source = "missing"
        against_wall_reference_sources[against_wall_reference_source] += 1
        condition_metadata = {
            "architecture_condition_has_floor_or_room_mask": bool(boundary),
            "architecture_condition_has_boundary_contour": bool(derived_wall_segments),
            "raw_wall_anchor_count": raw_wall_anchor_count,
            "derived_wall_segment_count": len(derived_wall_segments),
            "against_wall_reference_source": against_wall_reference_source,
            "door_anchor_count": len(architecture_anchors.get("doors", [])),
            "window_anchor_count": len(architecture_anchors.get("windows", [])),
            "boundary_source": boundary_source,
            "floor_mesh_source": boundary_source == "floor_mesh",
            "boundary_polygon_area": polygon_area(boundary),
        }
        if condition_metadata["architecture_condition_has_floor_or_room_mask"]:
            architecture_condition_floor_mask_count += 1
        if condition_metadata["architecture_condition_has_boundary_contour"]:
            architecture_condition_boundary_contour_count += 1

        semantic_path = dirs["semantic"] / f"{scene_id}.semantic_layout.png"
        rendered = render_scene_png(semantic_path, entities, boundary, args.image_size, palette)
        architecture_condition_path = dirs["arch_condition"] / f"{scene_id}.architecture_condition.png"
        render_architecture_condition_png(
            architecture_condition_path,
            boundary,
            architecture_anchors,
            derived_wall_segments,
            args.image_size,
            palette,
        )
        preview_path = dirs["preview_scene"] / f"{scene_id}_preview.png"
        write_png(preview_path, args.image_size, args.image_size, rendered)
        contact_images.append(rendered)

        def anchor_record(entity: dict[str, Any]) -> dict[str, Any]:
            return {
                "instance_id": entity["instance_id"],
                "anchor_type": entity.get("anchor_type") or "opening",
                "source_jid": entity.get("source_jid"),
                "raw_category": entity.get("raw_category"),
                "raw_title": entity.get("raw_title"),
                "reference_category": entity.get("reference_category"),
                "transform_source": entity.get("transform_source"),
                "size_source": entity.get("size_source"),
                "center": entity.get("center_m"),
                "size": entity.get("size_m"),
                "orientation": entity.get("orientation"),
                "footprint_m": entity.get("footprint_m"),
            }

        serialized_anchors = {key: [anchor_record(item) for item in value] for key, value in architecture_anchors.items()}
        serialized_anchors.setdefault("walls", [])
        serialized_anchors["walls"].extend(derived_wall_segments)
        arch = {
            "schema_version": "architecture-v1",
            "architecture_id": scene_id,
            "room_type": room_type,
            "metadata": {
                "architecture_anchor_candidates": serialized_anchors,
                "anchor_policy": "door/window/wall/floor/opening are architecture condition, not furniture entities",
                "derived_wall_segments": derived_wall_segments,
                "architecture_condition_metadata": condition_metadata,
            },
            "image_size_px": [args.image_size, args.image_size],
            "coordinate_system": {
                "source": "3D-FRONT",
                "axes": "x-z topdown candidate",
                "unit": "unknown_or_meter_candidate",
            },
            "boundary": {"polygon_m": boundary},
            "anchors": [item for values in serialized_anchors.values() for item in values],
            "architecture_anchors": serialized_anchors,
            "architecture_condition_metadata": condition_metadata,
            "source_scene_uid": scene.get("uid"),
            "boundary_source": boundary_source,
            "warnings": warnings,
        }
        arch_path = dirs["arch"] / f"{scene_id}.architecture_v1.json"
        write_json(arch_path, arch)

        observed_entities = []
        for entity in entities:
            observed_entities.append(
                {
                    "instance_id": entity["instance_id"],
                    "category": entity["category"],
                    "bbox_px": entity["bbox_px"],
                    "area_px": entity["area_px"],
                    "source_jid": entity["source_jid"],
                    "center": entity["center_m"],
                    "size": entity["size_m"],
                    "footprint": entity["footprint_m"],
                    "mapping_status": entity["mapping_status"],
                    "raw_category": entity["raw_category"],
                    "raw_super_category": entity["raw_super_category"],
                    "raw_title": entity["raw_title"],
                    "reference_category": entity["reference_category"],
                    "loreflection_category": entity["loreflection_category"],
                    "mapping_action": entity["mapping_action"],
                    "semantic_group": entity["semantic_group"],
                    "transform_source": entity["transform_source"],
                    "size_source": entity["size_source"],
                    "is_lamp": entity["is_lamp"],
                    "palette_alias_used": entity["palette_alias_used"],
                    "uncertainty": "prototype_fallback_geometry",
                }
            )
        observed = {
            "schema_version": "observed-lostate-v1",
            "state_role": "observed",
            "metadata": {"task_id": scene_id, "repair_round": 0, "source": "real_val50_prototype_v1"},
            "architecture_ref": {"architecture_id": scene_id, "path": rel(arch_path, output_root)},
            "semantic_registry_ref": {
                "palette_id": "indoor_palette_v1",
                "category_set": "loreflection_toy_palette_v1",
                "relation_set": "prototype_spatial_relations_v1",
            },
            "room_type": room_type,
            "furniture_instances": observed_entities,
            "measured_relations": [],
            "hard_constraint_evidence": [],
            "warnings": warnings,
        }
        observed_path = dirs["observed"] / f"{scene_id}.observed_lostate_v1.json"
        write_json(observed_path, observed)

        entities_per_scene[scene_id] = len(observed_entities)
        lamp_entities_per_scene[scene_id] = sum(1 for item in observed_entities if item.get("is_lamp"))
        all_warnings[scene_id] = warnings
        samples.append(
            {
                "scene_id": scene_id,
                "source_json": rel(source_copy, output_root),
                "architecture_json": rel(arch_path, output_root),
                "architecture_condition": rel(architecture_condition_path, output_root),
                "semantic_layout": rel(semantic_path, output_root),
                "observed_lostate": rel(observed_path, output_root),
                "preview": rel(preview_path, output_root),
                "warnings": warnings,
            }
        )
        mark_progress(f"scene_done:{scene_id}")

    contact_path = output_root / "preview" / "contact_sheet.png"
    make_contact_sheet(contact_images, contact_path, args.image_size)
    mark_progress("wrote_contact_sheet")

    jid_report = {
        "sampled_scene_count": len(samples),
        "total_furniture_entries": total_furniture,
        "valid_jid_count": valid_jid,
        "matched_jid_count": matched_jid,
        "unmatched_jid_count": unmatched_jid,
        "empty_jid_count": empty_jid,
        "match_rate_valid_jid": (matched_jid / valid_jid) if valid_jid else 0.0,
        "matched_examples": matched_examples,
        "unmatched_examples": unmatched_examples,
        "category_histogram": dict(category_histogram.most_common()),
        "reference_category_histogram": dict(reference_category_histogram.most_common()),
        "raw_category_histogram": dict(raw_category_histogram.most_common()),
        "unknown_raw_category_histogram": dict(unknown_raw_category_histogram.most_common(50)),
        "skipped_accessory_histogram": dict(skipped_accessory_histogram.most_common(50)),
        "mapping_action_histogram": dict(action_counter.most_common()),
        "semantic_group_histogram": dict(semantic_group_counter.most_common()),
        "furniture_kept_by_semantic_group": dict(furniture_group_counter.most_common()),
        "skipped_by_semantic_group": dict(skipped_group_counter.most_common()),
        "skipped_by_reason": dict(skip_reason_counter.most_common()),
        "legacy_action_histogram": dict(legacy_action_counter.most_common()),
        "mapping_status_histogram": dict(mapping_counter),
        "transform_source_histogram": dict(transform_source_counter.most_common()),
        "size_source_histogram": dict(size_source_counter.most_common()),
        "palette_alias_used_count": palette_alias_used_count,
    }
    jid_report_path = dirs["mapping"] / "jid_mapping_report.json"
    write_json(jid_report_path, jid_report)

    manifest = {
        "manifest_version": "real_val50_prototype_v1",
        "interface_tag": "interface-freeze-v1",
        "data_source_name": "EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle",
        "data_source_note": "official-like structure, not claimed as freshly downloaded official archive",
        "source_bundle": {
            "dataset_bundle_root": dataset_bundle.as_posix(),
            "threed_front_root": front_root.as_posix(),
            "threed_future_root": future_root.as_posix(),
            "threed_future_model_info": dataset_paths.future_model_info.as_posix(),
            "texture_root": texture_root.as_posix(),
            "dataset_root_source": "paths.local.env",
            "dataset_lock_id": "3dfront_a800_v1",
        },
        "selection": {
            "mode": "scene_ids_file" if requested_scene_ids else "scored_seed_sample",
            "requested_scene_ids": requested_scene_ids,
            "resolved_scene_ids": [sample["scene_id"] for sample in samples],
            "seed": args.seed,
        },
        "num_scenes": len(samples),
        "samples": samples,
    }
    if has_absolute_marker(manifest["samples"]):
        raise RuntimeError("Manifest sample paths contain forbidden absolute path markers.")
    write_json(output_root / "manifest.json", manifest)

    conversion_report = {
        "schema_version": "real-val50-prototype-conversion-report-v1",
        "pipeline": {
            "pipeline_type": "source-level native preprocessing",
            "native_builder_entry": "loreflection.builders.scene_package_builder",
            "raw_3dfront_read": True,
            "raw_3dfuture_read": True,
            "semlayoutdiff_processed_png_dependency": False,
            "output_level_adapter_dependency": False,
        },
        "selection": {
            "mode": "scene_ids_file" if requested_scene_ids else "scored_seed_sample",
            "requested_scene_ids": requested_scene_ids,
            "resolved_scene_ids": [sample["scene_id"] for sample in samples],
            "seed": args.seed,
        },
        "selected_scene_ids": [sample["scene_id"] for sample in samples],
        "model_info": {
            "model_count": model_index["num_models"],
            "category_fields": model_index.get("category_fields", []),
            "output_path": rel(model_index_path, output_root),
        },
        "jid_mapping_report": rel(jid_report_path, output_root),
        "architecture": {
            "generated_count": len(samples),
            "boundary_source_summary": dict(boundary_sources),
            "room_type_extracted_count": room_type_extracted,
            "architecture_condition_generated_count": len(samples),
            "door_anchor_count": door_anchor_count,
            "window_anchor_count": window_anchor_count,
            "wall_anchor_count": wall_anchor_count,
            "raw_wall_anchor_count": wall_anchor_count,
            "derived_wall_segment_count": derived_wall_segment_count_total,
            "architecture_condition_has_floor_or_room_mask_count": architecture_condition_floor_mask_count,
            "architecture_condition_has_boundary_contour_count": architecture_condition_boundary_contour_count,
            "against_wall_reference_source_summary": dict(against_wall_reference_sources.most_common()),
        },
        "semantic_layout": {
            "generated_count": len(samples),
            "drawable_furniture_count": drawable_count,
            "skipped_furniture_count": skipped_count,
            "unknown_category_count": unknown_count,
            "raw_total_objects": total_furniture,
            "furniture_kept_total": sum(furniture_group_counter.values()),
            "furniture_kept_by_semantic_group": dict(furniture_group_counter.most_common()),
            "architecture_kept_by_type": dict(architecture_type_counter.most_common()),
            "skipped_total": sum(skipped_group_counter.values()),
            "skipped_by_semantic_group": dict(skipped_group_counter.most_common()),
            "skipped_by_reason": dict(skip_reason_counter.most_common()),
            "architecture_anchor_candidates": action_counter.get("keep_architecture_anchor", 0),
            "core_furniture_kept": furniture_group_counter.get("core_furniture", 0),
            "lamp_kept": furniture_group_counter.get("lighting", 0),
            "accessory_skipped": skipped_group_counter.get("accessory", 0),
            "unknown_skipped": skipped_group_counter.get("unknown", 0),
            "legacy_compatibility_fields_note": "core_furniture_kept/lamp_kept/accessory_skipped/unknown_skipped are derived from semantic_group.",
            "core_unknown_count": core_unknown_count,
            "lamp_unknown_count": lamp_unknown_count,
            "semantic_drawn_count": semantic_drawn_count,
            "semantic_skipped_count": semantic_skipped_count,
            "palette_alias_used_count": palette_alias_used_count,
            "raw_category_histogram": dict(raw_category_histogram.most_common(50)),
            "reference_category_histogram": dict(reference_category_histogram.most_common(50)),
            "loreflection_category_histogram": dict(category_histogram.most_common(50)),
            "top_unknown_raw_categories": dict(unknown_raw_category_histogram.most_common(30)),
            "top_skipped_accessory_categories": dict(skipped_accessory_histogram.most_common(30)),
            "mapping_action_histogram": dict(action_counter.most_common()),
            "semantic_group_histogram": dict(semantic_group_counter.most_common()),
            "legacy_action_histogram": dict(legacy_action_counter.most_common()),
        },
        "transform_extraction": {
            "transform_source_summary": dict(transform_source_counter.most_common()),
            "size_source_summary": dict(size_source_counter.most_common()),
            "best_link_rule_used": "child.ref -> furniture.uid",
            "core_missing_transform_count": core_missing_transform_count,
            "lamp_missing_transform_count": lamp_missing_transform_count,
            "noncore_missing_transform_count": noncore_missing_transform_count,
        },
        "observed_lostate": {
            "generated_count": len(samples),
            "entities_per_scene": entities_per_scene,
            "lamp_entities_per_scene": lamp_entities_per_scene,
            "validation_status": "schema-compatible-minimal-fields",
        },
        "preview": {
            "contact_sheet": rel(contact_path, output_root),
            "per_scene": [sample["preview"] for sample in samples],
        },
        "warnings": all_warnings,
        "safety": {
            "downloaded_data": False,
            "downloaded_models": False,
            "training_started": False,
            "full_conversion_started": False,
        },
    }
    write_json(dirs["reports"] / "conversion_report.json", conversion_report)
    write_json(
        dirs["reports"] / "field_warnings.json",
        {
            "schema_version": "field-warnings-v1",
            "summary": {
                "raw_total_objects": total_furniture,
                "furniture_kept_total": sum(furniture_group_counter.values()),
                "furniture_kept_by_semantic_group": dict(furniture_group_counter.most_common()),
                "architecture_kept_by_type": dict(architecture_type_counter.most_common()),
                "skipped_total": sum(skipped_group_counter.values()),
                "skipped_by_semantic_group": dict(skipped_group_counter.most_common()),
                "skipped_by_reason": dict(skip_reason_counter.most_common()),
                "architecture_anchor_candidates": action_counter.get("keep_architecture_anchor", 0),
                "core_furniture_kept": furniture_group_counter.get("core_furniture", 0),
                "lamp_kept": furniture_group_counter.get("lighting", 0),
                "accessory_skipped": skipped_group_counter.get("accessory", 0),
                "unknown_skipped": skipped_group_counter.get("unknown", 0),
                "legacy_compatibility_fields_note": "legacy compatibility fields are derived from semantic_group.",
                "core_missing_transform_count": core_missing_transform_count,
                "lamp_missing_transform_count": lamp_missing_transform_count,
                "noncore_missing_transform_count": noncore_missing_transform_count,
                "palette_alias_used_count": palette_alias_used_count,
                "top_unknown_raw_categories": dict(unknown_raw_category_histogram.most_common(30)),
                "top_skipped_accessory_categories": dict(skipped_accessory_histogram.most_common(30)),
            },
            "warnings": all_warnings,
        },
    )
    maybe_write_comparison_report(output_root, conversion_report, jid_report)
    mark_progress("build_complete")

    print(f"Built real val50 prototype with {len(samples)} scene(s) at {output_root}")
    return conversion_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True, help="Server paths.local.env file.")
    parser.add_argument("--output-root", type=Path, required=True, help="Prototype output root.")
    parser.add_argument("--num-scenes", type=int, default=5, help="Bounded number of scenes to convert.")
    parser.add_argument("--scene-ids-file", type=Path, help="Optional fixed scene id list, one id per line. Preserves file order.")
    parser.add_argument("--seed", type=int, default=42, help="Sampling seed.")
    parser.add_argument("--image-size", type=int, default=512, help="PNG output size.")
    parser.add_argument("--strict", action="store_true", help="Fail if the requested number of scenes cannot be selected.")
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
