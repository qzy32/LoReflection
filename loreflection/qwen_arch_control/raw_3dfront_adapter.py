"""Adapt raw 3D-FRONT rooms into Architecture JSON and layout JSON."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from loreflection.builders.scene_package_builder import vec3, yaw_from_rotation
from loreflection.qwen_arch_control.metric_transform import build_metric_transform, world_to_pixel
from loreflection.semantic_registry import SemanticRegistry, load_registry


CATEGORY_RULES = [
    ("kids_bed", ("kids bed", "bunk bed", "crib")),
    ("single_bed", ("single bed",)),
    ("double_bed", ("king-size bed", "king size bed", "double bed", "bed")),
    ("corner_side_table", ("corner/side table", "corner side table", "side table")),
    ("round_end_table", ("round end table",)),
    ("coffee_table", ("coffee table",)),
    ("console_table", ("console table",)),
    ("tv_stand", ("tv stand", "media unit")),
    ("dressing_table", ("dressing table",)),
    ("dining_table", ("dining table",)),
    ("desk", ("desk",)),
    ("stool", ("stool", "footstool")),
    ("dressing_chair", ("dressing chair",)),
    ("dining_chair", ("dining chair",)),
    ("chinese_chair", ("chinese chair",)),
    ("armchair", ("armchair",)),
    ("lounge_chair", ("lounge chair", "cafe chair", "office chair")),
    ("chair", ("chair",)),
    ("loveseat_sofa", ("loveseat",)),
    ("lazy_sofa", ("lazy sofa",)),
    ("multi_seat_sofa", ("multi-seat sofa", "multi seat sofa")),
    ("chaise_longue_sofa", ("chaise longue",)),
    ("l_shaped_sofa", ("l-shaped sofa", "l shaped sofa")),
    ("sofa", ("sofa",)),
    ("nightstand", ("nightstand", "night stand", "bedside")),
    ("bookshelf", ("bookshelf", "bookcase")),
    ("shelf", ("shelf",)),
    ("children_cabinet", ("children cabinet",)),
    ("wine_cabinet", ("wine cabinet",)),
    ("wardrobe", ("wardrobe", "closet")),
    ("cabinet", ("cabinet", "sideboard", "drawer chest")),
    ("pendant_lamp", ("pendant lamp", "pendant light")),
    ("ceiling_lamp", ("ceiling lamp", "ceiling light")),
    ("table", ("table",)),
]
SIZE_PRIORS = {
    "double_bed": (2.0, 1.6),
    "single_bed": (1.9, 1.0),
    "kids_bed": (1.6, 0.8),
    "sofa": (2.0, 0.9),
    "multi_seat_sofa": (2.4, 1.0),
    "l_shaped_sofa": (2.4, 1.8),
    "table": (1.2, 0.8),
    "dining_table": (1.6, 0.9),
    "chair": (0.6, 0.6),
    "wardrobe": (1.4, 0.6),
    "cabinet": (1.2, 0.5),
}


def _text(*values: Any) -> str:
    return " ".join(str(value or "").lower().replace("_", " ") for value in values)


def map_frozen_category(
    furniture: dict[str, Any],
    model_info: dict[str, Any] | None,
    registry: SemanticRegistry,
) -> tuple[str | None, str | None]:
    model_info = model_info or {}
    text = _text(
        model_info.get("category"),
        model_info.get("super-category"),
        model_info.get("super_category"),
        furniture.get("title"),
        furniture.get("type"),
    )
    for category, tokens in CATEGORY_RULES:
        if category in registry.name_to_id and any(token in text for token in tokens):
            return category, None
    return None, None


def _mesh_points(mesh: dict[str, Any]) -> list[tuple[float, float]]:
    xyz = mesh.get("xyz")
    if not isinstance(xyz, list):
        return []
    raw = xyz if xyz and isinstance(xyz[0], list) else [xyz[i : i + 3] for i in range(0, len(xyz), 3)]
    points = []
    for point in raw:
        if isinstance(point, list) and len(point) >= 3:
            try:
                points.append((float(point[0]), float(point[2])))
            except (TypeError, ValueError):
                pass
    return points


def collect_room_child_openings_sem_layoutdiff_style(
    scene_json: dict[str, Any],
    room_json: dict[str, Any],
    *,
    assigned_room_id: str,
) -> list[dict[str, Any]]:
    """Collect Door/Window anchors using SemLayoutDiff's room-children policy.

    3D-FRONT stores meshes at scene scope, but SemLayoutDiff attaches extra
    meshes to a room only when the current room.children list references them.
    Scene-global Door/Window meshes that are not referenced by this room are
    intentionally ignored here.
    """
    meshes_in_scene = {
        str(mesh.get("uid")): mesh
        for mesh in scene_json.get("mesh", [])
        if isinstance(mesh, dict) and mesh.get("uid") is not None
    }
    anchors: list[dict[str, Any]] = []
    children = room_json.get("children", []) if isinstance(room_json.get("children"), list) else []
    for child in children:
        if not isinstance(child, dict):
            continue
        ref = str(child.get("ref"))
        mesh = meshes_in_scene.get(ref)
        if not isinstance(mesh, dict):
            continue
        mesh_type = mesh.get("type")
        if mesh_type not in {"Door", "Window"}:
            continue
        points = _mesh_points(mesh)
        if not points:
            continue
        anchor_type = "door" if mesh_type == "Door" else "window"
        bbox_m = [min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)]
        anchors.append(
            {
                "anchor_id": str(mesh.get("uid")),
                "anchor_type": anchor_type,
                "source": "room_child_mesh",
                "source_policy": "semlayoutdiff_room_children_only",
                "source_id": str(mesh.get("uid")),
                "source_object_id": str(mesh.get("uid")),
                "mesh_type": mesh_type,
                "assigned_room_id": assigned_room_id,
                "polygon_m": [[float(x), float(z)] for x, z in points],
                "bbox_m": bbox_m,
                "confidence": 1.0,
            }
        )
    return anchors


def _rect_from_points(points: list[tuple[float, float]]) -> list[list[float]]:
    xs = [point[0] for point in points]
    zs = [point[1] for point in points]
    return [[min(xs), min(zs)], [max(xs), min(zs)], [max(xs), max(zs)], [min(xs), max(zs)]]


def _world_to_px(point: tuple[float, float], boundary: list[list[float]], image_size: int, margin: int = 10) -> tuple[int, int]:
    xs = [p[0] for p in boundary]
    zs = [p[1] for p in boundary]
    scale = min(
        (image_size - 2 * margin) / max(max(xs) - min(xs), 1e-6),
        (image_size - 2 * margin) / max(max(zs) - min(zs), 1e-6),
    )
    x = margin + (point[0] - min(xs)) * scale
    y = image_size - (margin + (point[1] - min(zs)) * scale)
    return int(round(x)), int(round(y))


def _oriented_footprint_m(center: tuple[float, float], size: tuple[float, float], orientation_deg: float) -> list[list[float]]:
    cx, cz = center
    w, d = size
    theta = math.radians(float(orientation_deg))
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    return [[cx + dx * cos_t - dz * sin_t, cz + dx * sin_t + dz * cos_t] for dx, dz in corners]


def _bbox_from_px(points: list[tuple[int, int]], image_size: int) -> list[int]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [max(0, min(xs)), max(0, min(ys)), min(image_size - 1, max(xs)), min(image_size - 1, max(ys))]


def _bbox_px(center: tuple[float, float], size: tuple[float, float], boundary: list[list[float]], image_size: int) -> list[int]:
    corners = [
        (center[0] - size[0] / 2, center[1] - size[1] / 2),
        (center[0] + size[0] / 2, center[1] + size[1] / 2),
    ]
    pixels = [_world_to_px(point, boundary, image_size) for point in corners]
    return _bbox_from_px(pixels, image_size)


def _bbox_px_metric(center: tuple[float, float], size: tuple[float, float], orientation_deg: float, transform: dict[str, Any], image_size: int) -> tuple[list[int], list[list[float]], list[list[int]]]:
    footprint_m = _oriented_footprint_m(center, size, orientation_deg)
    footprint_px = [list(world_to_pixel((point[0], point[1]), transform)) for point in footprint_m]
    return _bbox_from_px([tuple(point) for point in footprint_px], image_size), footprint_m, footprint_px


def _size_m(furniture: dict[str, Any], transform: dict[str, Any], category: str) -> tuple[float, float]:
    size = vec3(furniture.get("size"))
    if size:
        return max(0.15, abs(size[0])), max(0.15, abs(size[2]))
    bbox = furniture.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 3:
        return max(0.15, abs(float(bbox[0]))), max(0.15, abs(float(bbox[2])))
    if isinstance(bbox, list) and len(bbox) >= 6:
        return max(0.15, abs(float(bbox[3]) - float(bbox[0]))), max(0.15, abs(float(bbox[5]) - float(bbox[2])))
    prior = SIZE_PRIORS.get(category, (0.8, 0.6))
    scale = vec3(transform.get("scale")) or (1.0, 1.0, 1.0)
    return max(0.15, prior[0] * abs(scale[0])), max(0.15, prior[1] * abs(scale[2]))


def _room_type(raw: Any) -> str:
    text = str(raw or "room").lower().replace(" ", "")
    if "bed" in text:
        return "bedroom"
    if "living" in text:
        return "livingroom"
    if "dining" in text:
        return "diningroom"
    if "library" in text or "study" in text:
        return "study"
    return text or "room"


def adapt_scene_file(
    scene_path: Path,
    model_index: dict[str, dict[str, Any]],
    image_size: int = 256,
    registry: SemanticRegistry | None = None,
    renderer_version: str = "normalized_v1",
    canvas_extent_m: float | None = None,
) -> list[dict[str, Any]]:
    registry = registry or load_registry()
    scene = json.loads(scene_path.read_text(encoding="utf-8", errors="ignore"))
    scene_id = str(scene.get("uid") or scene_path.stem).replace("/", "_")
    furniture_by_uid = {
        str(item.get("uid")): item for item in scene.get("furniture", []) if isinstance(item, dict)
    }
    mesh_by_uid = {str(item.get("uid")): item for item in scene.get("mesh", []) if isinstance(item, dict)}
    rooms = scene.get("scene", {}).get("room") or scene.get("scene", {}).get("rooms") or []
    adapted = []
    for room_index, room in enumerate(rooms if isinstance(rooms, list) else []):
        if not isinstance(room, dict) or room.get("empty") is True:
            continue
        linked_furniture = []
        linked_meshes = []
        for child in room.get("children", []) if isinstance(room.get("children"), list) else []:
            if not isinstance(child, dict):
                continue
            ref = str(child.get("ref"))
            if ref in furniture_by_uid:
                linked_furniture.append((child, furniture_by_uid[ref]))
            if ref in mesh_by_uid:
                linked_meshes.append((child, mesh_by_uid[ref]))

        floor_points = [
            point
            for _, mesh in linked_meshes
            if "floor" in _text(mesh.get("type"), mesh.get("uid"), mesh.get("jid"))
            for point in _mesh_points(mesh)
        ]
        warnings = []
        provisional = []
        skipped = []
        for child, furniture in linked_furniture:
            jid = str(furniture.get("jid") or "")
            category, architecture_type = map_frozen_category(furniture, model_index.get(jid), registry)
            position = vec3(child.get("pos") or child.get("position") or child.get("translate"))
            if not position:
                skipped.append({"source_object_id": furniture.get("uid"), "reason": "missing_position"})
                continue
            center = (position[0], position[2])
            if not category:
                skipped.append(
                    {
                        "source_object_id": furniture.get("uid"),
                        "jid": jid,
                        "reason": "unmapped_frozen_category",
                        "raw_category": (model_index.get(jid) or {}).get("category"),
                        "title": furniture.get("title"),
                    }
                )
                continue
            provisional.append((category, center, _size_m(furniture, child, category), furniture, child))

        if floor_points:
            boundary_m = _rect_from_points(floor_points)
            boundary_source = "room_floor_mesh"
        elif provisional:
            extent_points = []
            for _, center, size, _, _ in provisional:
                extent_points.extend(
                    [
                        (center[0] - size[0] / 2 - 0.5, center[1] - size[1] / 2 - 0.5),
                        (center[0] + size[0] / 2 + 0.5, center[1] + size[1] / 2 + 0.5),
                    ]
                )
            boundary_m = _rect_from_points(extent_points)
            boundary_source = "furniture_extent_fallback"
            warnings.append("room floor mesh unavailable; boundary derived from furniture extents")
        else:
            continue
        metric_transform = None
        if renderer_version == "metric_v2":
            metric_transform = build_metric_transform(boundary_m, image_size, canvas_extent_m=canvas_extent_m)
            boundary_px = [list(world_to_pixel(tuple(point), metric_transform)) for point in boundary_m]
        else:
            boundary_px = [list(_world_to_px(tuple(point), boundary_m, image_size)) for point in boundary_m]

        objects = []
        for object_index, (category, center, size, furniture, child) in enumerate(provisional):
            orientation_deg = math.degrees(yaw_from_rotation(child.get("rot") or child.get("rotation")))
            if metric_transform:
                bbox_px, footprint_m, footprint_px = _bbox_px_metric(center, size, orientation_deg, metric_transform, image_size)
            else:
                bbox_px = _bbox_px(center, size, boundary_m, image_size)
                footprint_m = _oriented_footprint_m(center, size, orientation_deg)
                footprint_px = [list(_world_to_px(tuple(point), boundary_m, image_size)) for point in footprint_m]
            objects.append(
                {
                    "instance_id": str(child.get("instanceid") or furniture.get("uid") or f"object_{object_index:03d}"),
                    "category": category,
                    "bbox_px": bbox_px,
                    "footprint_m": footprint_m,
                    "footprint_px": footprint_px,
                    "center_m": [center[0], center[1]],
                    "size_m": [size[0], size[1]],
                    "orientation_deg": orientation_deg,
                    "source_object_id": str(furniture.get("uid") or ""),
                    "source_json_path": str(scene_path),
                }
            )
        if len(objects) < 2:
            continue

        sample_id = f"{scene_id}_room_{room_index:02d}"
        anchors = collect_room_child_openings_sem_layoutdiff_style(scene, room, assigned_room_id=sample_id)
        door_anchor_count = sum(1 for anchor in anchors if anchor["anchor_type"] == "door")
        window_anchor_count = sum(1 for anchor in anchors if anchor["anchor_type"] == "window")
        architecture = {
            "schema_version": "architecture-v2-p0",
            "architecture_id": sample_id,
            "scene_id": scene_id,
            "house_id": scene.get("jobid"),
            "floorplan_id": scene_id,
            "room_type": _room_type(room.get("type")),
            "image_size_px": [image_size, image_size],
            "boundary": {"polygon_m": boundary_m, "polygon_px": boundary_px, "source": boundary_source, "boundary_source": boundary_source},
            "metric_transform": metric_transform,
            "anchors": anchors,
            "opening_source_policy": "semlayoutdiff_room_children_only",
            "door_anchor_count": door_anchor_count,
            "window_anchor_count": window_anchor_count,
            "native_room_child_door_count": door_anchor_count,
            "native_room_child_window_count": window_anchor_count,
            "has_room_child_door": door_anchor_count > 0,
            "has_room_child_window": window_anchor_count > 0,
            "source": {"kind": "raw_3dfront", "source_scene_json": str(scene_path), "room_index": room_index},
        }
        layout = {
            "schema_version": "layout-json-v1",
            "layout_id": f"{sample_id}_layout",
            "sample_id": sample_id,
            "scene_id": scene_id,
            "house_id": scene.get("jobid"),
            "floorplan_id": scene_id,
            "room_type": architecture["room_type"],
            "image_size_px": [image_size, image_size],
            "objects": objects,
            "skipped_objects": skipped,
            "metric_transform": metric_transform,
            "source": {"kind": "raw_3dfront", "source_scene_json": str(scene_path), "room_index": room_index},
        }
        adapted.append(
            {
                "sample_id": sample_id,
                "scene_id": scene_id,
                "house_id": scene.get("jobid"),
                "floorplan_id": scene_id,
                "room_type": architecture["room_type"],
                "source_scene_json": str(scene_path),
                "architecture": architecture,
                "layout": layout,
                "warnings": warnings,
                "skipped_objects": skipped,
            }
        )
    return adapted
