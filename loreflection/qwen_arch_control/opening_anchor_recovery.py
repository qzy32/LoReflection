"""Recover scene-level 3D-FRONT openings for per-room Architecture JSON."""

from __future__ import annotations

import math
from typing import Any

from loreflection.builders.scene_package_builder import vec3
from loreflection.qwen_arch_control.metric_transform import world_to_pixel

FALSE_DOOR_TOKENS = (
    "wardrobe door",
    "cabinet door",
    "drawer door",
    "shower door",
    "appliance door",
    "refrigerator door",
    "fridge door",
    "oven door",
    "dishwasher door",
    "washer door",
    "washing machine door",
    "door shelf",
)
STRUCTURAL_DOOR_TOKENS = (
    "door/entry",
    "entry door",
    "swing door",
    "sliding door",
    "double swing door",
    "single swing door",
    "room door",
)
WINDOW_TOKENS = ("window", "bay window", "casement", "sash")


def _text(*values: Any) -> str:
    return " ".join(str(value or "").lower().replace("_", " ") for value in values)


def _mesh_points(mesh: dict[str, Any]) -> list[tuple[float, float]]:
    xyz = mesh.get("xyz")
    if not isinstance(xyz, list):
        return []
    raw = xyz if xyz and isinstance(xyz[0], list) else [xyz[i : i + 3] for i in range(0, len(xyz), 3)]
    points: list[tuple[float, float]] = []
    for point in raw:
        if isinstance(point, list) and len(point) >= 3:
            try:
                points.append((float(point[0]), float(point[2])))
            except (TypeError, ValueError):
                pass
    return points


def _bbox_from_points(points: list[tuple[float, float]]) -> list[float] | None:
    if not points:
        return None
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]
    return [min(xs), min(zs), max(xs), max(zs)]


def _rect_from_bbox(bbox: list[float]) -> list[list[float]]:
    x0, z0, x1, z1 = bbox
    return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]


def _opening_type_from_text(text: str, *, source_kind: str) -> str | None:
    normalized = text.lower().replace("_", " ")
    if any(token in normalized for token in WINDOW_TOKENS):
        return "window"
    if "door" not in normalized:
        return None
    if any(token in normalized for token in FALSE_DOOR_TOKENS):
        return None
    if source_kind == "mesh":
        return "door"
    if any(token in normalized for token in STRUCTURAL_DOOR_TOKENS):
        return "door"
    return None


def _size_from_furniture(furniture: dict[str, Any]) -> tuple[float, float]:
    size = vec3(furniture.get("size"))
    if size:
        return max(0.12, abs(size[0])), max(0.08, abs(size[2]))
    bbox = furniture.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 3:
        return max(0.12, abs(float(bbox[0]))), max(0.08, abs(float(bbox[2])))
    if isinstance(bbox, list) and len(bbox) >= 6:
        return max(0.12, abs(float(bbox[3]) - float(bbox[0]))), max(0.08, abs(float(bbox[5]) - float(bbox[2])))
    return 0.85, 0.18


def collect_scene_opening_candidates(
    scene: dict[str, Any],
    model_index: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Collect explicit Door/Window candidates from scene mesh and structural furniture."""
    model_index = model_index or {}
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for mesh in scene.get("mesh", []) if isinstance(scene.get("mesh"), list) else []:
        if not isinstance(mesh, dict):
            continue
        raw_text = _text(mesh.get("type"), mesh.get("uid"), mesh.get("jid"), mesh.get("aid"))
        opening_type = _opening_type_from_text(raw_text, source_kind="mesh")
        if opening_type is None:
            continue
        points = _mesh_points(mesh)
        bbox = _bbox_from_points(points)
        if bbox is None:
            continue
        source_id = str(mesh.get("uid") or mesh.get("jid") or mesh.get("aid"))
        key = (opening_type, source_id)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "candidate_id": f"scene_mesh:{source_id}",
                "opening_type": opening_type,
                "source": "scene_global_mesh",
                "source_id": source_id,
                "raw_type": mesh.get("type"),
                "raw_name": mesh.get("uid") or mesh.get("jid"),
                "polygon_m": points,
                "bbox_m": bbox,
                "center_m": [(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0],
                "size_m": [max(0.0, bbox[2] - bbox[0]), max(0.0, bbox[3] - bbox[1])],
                "confidence_source": 1.0,
            }
        )

    furniture_by_uid = {str(item.get("uid")): item for item in scene.get("furniture", []) if isinstance(item, dict)}
    rooms = scene.get("scene", {}).get("room") or scene.get("scene", {}).get("rooms") or []
    for room_index, room in enumerate(rooms if isinstance(rooms, list) else []):
        if not isinstance(room, dict):
            continue
        for child in room.get("children", []) if isinstance(room.get("children"), list) else []:
            if not isinstance(child, dict):
                continue
            ref = str(child.get("ref"))
            furniture = furniture_by_uid.get(ref)
            if furniture is None:
                continue
            jid = str(furniture.get("jid") or "")
            info = model_index.get(jid) or {}
            raw_text = _text(
                furniture.get("title"),
                furniture.get("type"),
                info.get("category"),
                info.get("super-category"),
                info.get("super_category"),
            )
            opening_type = _opening_type_from_text(raw_text, source_kind="furniture")
            if opening_type is None:
                continue
            position = vec3(child.get("pos") or child.get("position") or child.get("translate"))
            if not position:
                continue
            sx, sz = _size_from_furniture(furniture)
            cx, cz = float(position[0]), float(position[2])
            bbox = [cx - sx / 2.0, cz - sz / 2.0, cx + sx / 2.0, cz + sz / 2.0]
            source_id = str(child.get("instanceid") or furniture.get("uid") or ref)
            key = (opening_type, source_id)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "candidate_id": f"scene_furniture:{source_id}",
                    "opening_type": opening_type,
                    "source": "scene_global_furniture",
                    "source_id": source_id,
                    "raw_type": furniture.get("type"),
                    "raw_name": furniture.get("title"),
                    "polygon_m": _rect_from_bbox(bbox),
                    "bbox_m": bbox,
                    "center_m": [cx, cz],
                    "size_m": [sx, sz],
                    "confidence_source": 0.8,
                    "source_room_index": room_index,
                }
            )
    return candidates


def _point_segment_distance(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def _nearest_boundary(point_candidates: list[tuple[float, float]], boundary: list[list[float]]) -> tuple[float, list[list[float]] | None]:
    if len(boundary) < 2:
        return float("inf"), None
    best = (float("inf"), None)
    pts = [(float(x), float(z)) for x, z in boundary]
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        for point in point_candidates:
            dist = _point_segment_distance(point, a, b)
            if dist < best[0]:
                best = (dist, [[a[0], a[1]], [b[0], b[1]]])
    return best


def _point_in_polygon(point: tuple[float, float], polygon: list[list[float]]) -> bool:
    x, y = point
    inside = False
    if len(polygon) < 3:
        return False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = float(polygon[i][0]), float(polygon[i][1])
        xj, yj = float(polygon[j][0]), float(polygon[j][1])
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _room_bbox(boundary: list[list[float]]) -> list[float]:
    xs = [float(p[0]) for p in boundary]
    zs = [float(p[1]) for p in boundary]
    return [min(xs), min(zs), max(xs), max(zs)]


def _bbox_expanded_intersects(candidate_bbox: list[float], room_bbox: list[float], buffer_m: float) -> bool:
    ax0, az0, ax1, az1 = candidate_bbox
    bx0, bz0, bx1, bz1 = room_bbox
    bx0 -= buffer_m
    bz0 -= buffer_m
    bx1 += buffer_m
    bz1 += buffer_m
    return not (ax1 < bx0 or ax0 > bx1 or az1 < bz0 or az0 > bz1)


def opening_assignment_debug(
    candidate: dict[str, Any],
    boundary_m: list[list[float]],
    *,
    boundary_buffer_width_m: float = 0.40,
) -> dict[str, Any]:
    bbox = [float(v) for v in candidate.get("bbox_m") or [0, 0, 0, 0]]
    center = tuple(float(v) for v in candidate.get("center_m") or [(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0])
    polygon = candidate.get("polygon_m") or _rect_from_bbox(bbox)
    points = [(float(x), float(z)) for x, z in polygon] + [center]
    distance, segment = _nearest_boundary(points, boundary_m)
    return {
        "candidate_id": candidate.get("candidate_id"),
        "opening_type": candidate.get("opening_type"),
        "source": candidate.get("source"),
        "source_id": candidate.get("source_id"),
        "distance_to_room_boundary_m": distance,
        "intersects_room_boundary_buffer": _bbox_expanded_intersects(bbox, _room_bbox(boundary_m), boundary_buffer_width_m) if boundary_m else False,
        "candidate_center_inside_room": _point_in_polygon(center, boundary_m),
        "nearest_boundary_segment_m": segment,
    }


def _project_point_to_segment(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> tuple[float, tuple[float, float]]:
    px, py = point
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return 0.0, a
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    return t, (ax + t * dx, ay + t * dy)


def _boundary_centroid(boundary: list[list[float]]) -> tuple[float, float]:
    if not boundary:
        return 0.0, 0.0
    return sum(float(p[0]) for p in boundary) / len(boundary), sum(float(p[1]) for p in boundary) / len(boundary)


def _project_opening_to_boundary_strip(
    candidate: dict[str, Any],
    boundary_m: list[list[float]],
    nearest_segment: list[list[float]] | None,
    *,
    min_length_m: float = 0.70,
    thickness_m: float = 0.12,
) -> list[list[float]] | None:
    """Project an opening candidate onto the assigned room boundary as an inward strip.

    Scene-level Door meshes can be vertical surfaces or include wall-thickness geometry.
    They are evidence for an opening, not the exact 2D semantic shape to draw.  The Qwen
    architecture condition should show a clean boundary-aligned strip.
    """
    if not nearest_segment or len(nearest_segment) != 2:
        return None
    a = (float(nearest_segment[0][0]), float(nearest_segment[0][1]))
    b = (float(nearest_segment[1][0]), float(nearest_segment[1][1]))
    vx, vz = b[0] - a[0], b[1] - a[1]
    seg_len = math.hypot(vx, vz)
    if seg_len <= 1e-6:
        return None
    tx, tz = vx / seg_len, vz / seg_len
    polygon = candidate.get("polygon_m") or _rect_from_bbox([float(v) for v in candidate.get("bbox_m") or [0, 0, 0, 0]])
    ts = []
    for x, z in polygon:
        t, _ = _project_point_to_segment((float(x), float(z)), a, b)
        ts.append(t * seg_len)
    center = candidate.get("center_m") or [sum(float(x) for x, _ in polygon) / len(polygon), sum(float(z) for _, z in polygon) / len(polygon)]
    center_t, _ = _project_point_to_segment((float(center[0]), float(center[1])), a, b)
    center_s = center_t * seg_len
    lo = min(ts) if ts else center_s - min_length_m / 2
    hi = max(ts) if ts else center_s + min_length_m / 2
    if hi - lo < min_length_m:
        lo = center_s - min_length_m / 2
        hi = center_s + min_length_m / 2
    lo = max(0.0, min(seg_len, lo))
    hi = max(0.0, min(seg_len, hi))
    if hi - lo < min_length_m:
        if lo <= 1e-6:
            hi = min(seg_len, lo + min_length_m)
        elif hi >= seg_len - 1e-6:
            lo = max(0.0, hi - min_length_m)
    p0 = (a[0] + tx * lo, a[1] + tz * lo)
    p1 = (a[0] + tx * hi, a[1] + tz * hi)
    # Pick the normal pointing toward room centroid, so the official semantic strip lies on the floor side.
    n1 = (-tz, tx)
    n2 = (tz, -tx)
    mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
    centroid = _boundary_centroid(boundary_m)
    to_centroid = (centroid[0] - mid[0], centroid[1] - mid[1])
    normal = n1 if (n1[0] * to_centroid[0] + n1[1] * to_centroid[1]) >= (n2[0] * to_centroid[0] + n2[1] * to_centroid[1]) else n2
    p0i = (p0[0] + normal[0] * thickness_m, p0[1] + normal[1] * thickness_m)
    p1i = (p1[0] + normal[0] * thickness_m, p1[1] + normal[1] * thickness_m)
    return [[p0[0], p0[1]], [p1[0], p1[1]], [p1i[0], p1i[1]], [p0i[0], p0i[1]]]


def _confidence(candidate: dict[str, Any], distance_m: float) -> float | None:
    source = str(candidate.get("source") or "")
    if source == "room_child_mesh":
        return 1.0
    if source == "scene_global_mesh":
        if distance_m <= 0.15:
            return 0.90
        if distance_m <= 0.35:
            return 0.75
        return None
    if source == "scene_global_furniture":
        if distance_m <= 0.25:
            return 0.70
        return None
    return None


def recover_opening_anchors_for_room(
    candidates: list[dict[str, Any]],
    boundary_m: list[list[float]],
    *,
    assigned_room_id: str,
    existing_anchors: list[dict[str, Any]] | None = None,
    metric_transform: dict[str, Any] | None = None,
    image_size: int = 256,
    boundary_buffer_width_m: float = 0.40,
    max_boundary_distance_m: float = 0.35,
) -> list[dict[str, Any]]:
    """Assign explicit scene-level openings to one room by boundary proximity."""
    existing_anchors = existing_anchors or []
    seen = {
        (str(a.get("anchor_type")), str(a.get("source_object_id") or a.get("source_id") or a.get("anchor_id")))
        for a in existing_anchors
    }
    recovered: list[dict[str, Any]] = []
    for candidate in candidates:
        opening_type = str(candidate.get("opening_type") or "")
        bbox = candidate.get("bbox_m")
        if opening_type not in {"door", "window"} or not bbox:
            continue
        debug = opening_assignment_debug(candidate, boundary_m, boundary_buffer_width_m=boundary_buffer_width_m)
        distance = float(debug["distance_to_room_boundary_m"])
        if distance > max_boundary_distance_m or not debug["intersects_room_boundary_buffer"]:
            continue
        confidence = _confidence(candidate, distance)
        if confidence is None:
            continue
        source_id = str(candidate.get("source_id") or candidate.get("candidate_id"))
        key = (opening_type, source_id)
        if key in seen:
            continue
        seen.add(key)
        raw_polygon_m = candidate.get("polygon_m") or _rect_from_bbox([float(v) for v in bbox])
        projected_polygon_m = _project_opening_to_boundary_strip(candidate, boundary_m, debug["nearest_boundary_segment_m"])
        polygon_m = projected_polygon_m or raw_polygon_m
        bbox_m = [float(v) for v in bbox]
        anchor: dict[str, Any] = {
            "anchor_id": f"recovered_{opening_type}_{source_id}",
            "anchor_type": opening_type,
            "source": f"{candidate.get('source')}_recovered",
            "source_id": source_id,
            "source_object_id": source_id,
            "assigned_room_id": assigned_room_id,
            "assignment_method": "boundary_distance_buffer_intersection",
            "confidence": confidence,
            "distance_to_room_boundary_m": distance,
            "raw_polygon_m": raw_polygon_m,
            "raw_bbox_m": bbox_m,
            "polygon_m": polygon_m,
            "projected_polygon_m": polygon_m,
            "nearest_boundary_segment_m": debug["nearest_boundary_segment_m"],
            "render_policy": "project_to_room_boundary_min_visible_strip",
        }
        if metric_transform:
            px = [world_to_pixel((float(x), float(z)), metric_transform) for x, z in polygon_m]
            if px:
                anchor["polygon_px"] = [[int(x), int(y)] for x, y in px]
                anchor["projected_polygon_px"] = [[int(x), int(y)] for x, y in px]
                anchor["bbox_px"] = [
                    max(0, min(x for x, _ in px)),
                    max(0, min(y for _, y in px)),
                    min(image_size - 1, max(x for x, _ in px)),
                    min(image_size - 1, max(y for _, y in px)),
                ]
        recovered.append(anchor)
    return recovered
