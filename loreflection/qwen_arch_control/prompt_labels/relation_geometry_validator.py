from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from loreflection.semantic_registry import SemanticRegistry, load_registry


def _bbox_from_object(obj: dict[str, Any]) -> tuple[float, float, float, float] | None:
    if obj.get("footprint_m"):
        pts = [(float(p[0]), float(p[1])) for p in obj["footprint_m"]]
        xs = [p[0] for p in pts]
        zs = [p[1] for p in pts]
        return min(xs), min(zs), max(xs), max(zs)
    if obj.get("center_m") and obj.get("size_m"):
        cx, cz = float(obj["center_m"][0]), float(obj["center_m"][1])
        sx, sz = float(obj["size_m"][0]), float(obj["size_m"][1])
        return cx - sx / 2, cz - sz / 2, cx + sx / 2, cz + sz / 2
    return None


def _center(box: tuple[float, float, float, float]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def _edge_gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dz = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dz)


def _center_distance(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ca = _center(a)
    cb = _center(b)
    return math.hypot(ca[0] - cb[0], ca[1] - cb[1])


def extract_category_instances_from_layout(layout_json: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    instances: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obj in layout_json.get("objects", []):
        category = obj.get("category")
        box = _bbox_from_object(obj)
        if not category or box is None:
            continue
        instances[str(category)].append(
            {
                "category": str(category),
                "instance_id": obj.get("instance_id"),
                "bbox_m": list(box),
                "centroid_m": list(_center(box)),
            }
        )
    return dict(instances)


def extract_category_instances_from_target_image(
    image_path: Path,
    registry: SemanticRegistry | None = None,
) -> dict[str, list[dict[str, Any]]]:
    registry = registry or load_registry()
    arr = np.asarray(Image.open(image_path).convert("RGB"), dtype=np.uint8)
    instances: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sid in registry.object_ids:
        category = registry.id_to_name[sid]
        color = np.asarray(registry.id_to_rgb[sid], dtype=np.uint8)
        mask = np.all(arr == color, axis=-1)
        for idx, box in enumerate(_connected_component_boxes(mask)):
            x0, y0, x1, y1 = box
            instances[category].append(
                {
                    "category": category,
                    "instance_id": f"{category}_cc_{idx}",
                    "bbox_px": [x0, y0, x1, y1],
                    "centroid_px": [(x0 + x1) / 2, (y0 + y1) / 2],
                }
            )
    return dict(instances)


def _connected_component_boxes(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    seen = np.zeros(mask.shape, dtype=bool)
    boxes: list[tuple[int, int, int, int]] = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(x, y)]
            seen[y, x] = True
            xs: list[int] = []
            ys: list[int] = []
            while stack:
                cx, cy = stack.pop()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((nx, ny))
            boxes.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1))
    return boxes


def compute_min_distance_between_instances(
    subject_instances: list[dict[str, Any]],
    object_instances: list[dict[str, Any]],
) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for sub in subject_instances:
        a = tuple(float(v) for v in sub["bbox_m"])
        for obj in object_instances:
            b = tuple(float(v) for v in obj["bbox_m"])
            edge = _edge_gap(a, b)
            center = _center_distance(a, b)
            evidence = {
                "subject_instance_id": sub.get("instance_id"),
                "object_instance_id": obj.get("instance_id"),
                "edge_gap_m": edge,
                "center_distance_m": center,
            }
            if best is None or edge < best["edge_gap_m"]:
                best = evidence
    return best or {"edge_gap_m": None, "center_distance_m": None}


def validate_near_relation(
    subject_instances: list[dict[str, Any]],
    object_instances: list[dict[str, Any]],
    *,
    subject_category: str = "",
    object_category: str = "",
    near_max_center_distance_m: float = 1.5,
    near_max_edge_gap_m: float = 0.8,
) -> dict[str, Any]:
    if not subject_instances or not object_instances:
        return {"status": "invalid", "reason": "missing_instances"}
    edge_threshold = 0.6 if "chair" in subject_category and "table" in object_category else near_max_edge_gap_m
    evidence = compute_min_distance_between_instances(subject_instances, object_instances)
    edge = evidence.get("edge_gap_m")
    center = evidence.get("center_distance_m")
    ok = bool(
        edge is not None
        and center is not None
        and (float(edge) <= edge_threshold or float(center) <= near_max_center_distance_m)
    )
    return {
        "status": "pass" if ok else "invalid",
        "reason": None if ok else "target_geometry_not_near",
        "evidence": evidence | {"edge_gap_threshold_m": edge_threshold, "center_threshold_m": near_max_center_distance_m},
    }


def validate_around_relation(
    subject_instances: list[dict[str, Any]],
    object_instances: list[dict[str, Any]],
    *,
    edge_gap_threshold_m: float = 0.8,
) -> dict[str, Any]:
    if not subject_instances or not object_instances:
        return {"status": "invalid", "reason": "missing_instances"}
    table = object_instances[0]
    tbox = tuple(float(v) for v in table["bbox_m"])
    tc = _center(tbox)
    near_count = 0
    quadrants: set[tuple[int, int]] = set()
    gaps: list[float] = []
    for sub in subject_instances:
        sbox = tuple(float(v) for v in sub["bbox_m"])
        gap = _edge_gap(sbox, tbox)
        gaps.append(gap)
        if gap <= edge_gap_threshold_m:
            near_count += 1
        sc = _center(sbox)
        quadrants.add((1 if sc[0] >= tc[0] else -1, 1 if sc[1] >= tc[1] else -1))
    needed = max(1, math.ceil(len(subject_instances) * 0.75))
    ok = near_count >= needed and len(quadrants) >= min(2, len(subject_instances))
    return {
        "status": "pass" if ok else "invalid",
        "reason": None if ok else "target_geometry_not_around",
        "evidence": {
            "near_count": near_count,
            "required_near_count": needed,
            "quadrant_count": len(quadrants),
            "edge_gaps_m": gaps,
            "edge_gap_threshold_m": edge_gap_threshold_m,
        },
    }


def validate_against_wall_relation(*_: Any, **__: Any) -> dict[str, Any]:
    return {"status": "unsupported", "route": "verifier_only_or_drop_from_prompt"}


def validate_clearance_relation(*_: Any, **__: Any) -> dict[str, Any]:
    return {"status": "unsupported", "route": "verifier_only_or_drop_from_prompt"}


def validate_pairwise_constraints_against_target(
    pairwise_constraints: list[dict[str, Any]],
    *,
    layout_json: dict[str, Any] | None = None,
    target_furniture_only_path: Path | None = None,
) -> dict[str, Any]:
    instances = extract_category_instances_from_layout(layout_json or {}) if layout_json else {}
    source = "layout_json"
    if not instances and target_furniture_only_path:
        instances = extract_category_instances_from_target_image(target_furniture_only_path)
        source = "target_mask"

    verified: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for rel in pairwise_constraints:
        subject = str(rel.get("subject", ""))
        predicate = str(rel.get("predicate", ""))
        obj = str(rel.get("object", ""))
        if predicate in {"near", "closely_near", "paired_with"}:
            result = validate_near_relation(
                instances.get(subject, []),
                instances.get(obj, []),
                subject_category=subject,
                object_category=obj,
            )
        elif predicate == "around":
            result = validate_around_relation(instances.get(subject, []), instances.get(obj, []))
        elif predicate in {"against_wall", "left_of", "right_of", "in_front_of", "behind", "facing", "main_anchor_of"}:
            result = {"status": "unsupported", "route": "verifier_only_or_drop_from_prompt"}
        elif predicate in {"away_from_door_clearance", "away_from_window_clearance", "accessible"}:
            result = validate_clearance_relation()
        else:
            result = {"status": "unsupported", "route": "verifier_only_or_drop_from_prompt"}

        entry = dict(rel)
        entry["geometry_validation"] = result
        entry["validation_source"] = source
        if result.get("status") == "pass":
            entry["source"] = "geometry_verified"
            entry["prompt_allowed"] = True
            verified.append(entry)
        else:
            entry["source"] = rel.get("source", "rule")
            entry["prompt_allowed"] = False
            entry["reason"] = result.get("reason") or result.get("route") or result.get("status")
            dropped.append(entry)
    return {"geometry_verified": verified, "dropped": dropped, "validation_source": source}
