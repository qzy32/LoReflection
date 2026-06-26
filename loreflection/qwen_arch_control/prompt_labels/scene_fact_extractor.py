from __future__ import annotations

from collections import Counter
from typing import Any


def infer_room_type(counts: dict[str, int], raw_room_type: str | None = None) -> tuple[str, str]:
    raw = str(raw_room_type or "").lower()
    if raw and raw not in {"unknown", "none", "room"}:
        return raw, "raw_scene"
    keys = set(counts)
    if keys & {"double_bed", "single_bed", "kids_bed", "nightstand"}:
        return "bedroom", "furniture_rule"
    if keys & {"sofa", "multi_seat_sofa", "coffee_table", "tv_stand", "armchair"}:
        return "livingroom", "furniture_rule"
    if keys & {"dining_table", "dining_chair"}:
        return "diningroom", "furniture_rule"
    if "desk" in keys and ("chair" in keys or "bookshelf" in keys):
        return "study", "furniture_rule"
    if keys & {"toilet", "wash_basin", "bathtub"}:
        return "bathroom", "furniture_rule"
    if keys & {"refrigerator", "stove", "sink"}:
        return "kitchen", "furniture_rule"
    if "washing_machine" in keys:
        return "balcony_or_laundry", "furniture_rule"
    return "unknown", "unknown"


def extract_scene_facts(layout: dict[str, Any], architecture: dict[str, Any], sample_id: str | None = None) -> dict[str, Any]:
    counts = Counter(str(obj.get("category")) for obj in layout.get("objects", []) if obj.get("category"))
    room_type, source = infer_room_type(dict(counts), layout.get("room_type") or architecture.get("room_type"))
    anchors = architecture.get("anchors", []) if isinstance(architecture.get("anchors"), list) else []
    has_door = any(str(a.get("anchor_type")) == "door" for a in anchors)
    has_window = any(str(a.get("anchor_type")) == "window" for a in anchors)
    primary = next(iter(counts), None)
    if any(k in counts for k in ("double_bed", "single_bed", "kids_bed")):
        primary = next(k for k in ("double_bed", "single_bed", "kids_bed") if k in counts)
    elif any(k in counts for k in ("sofa", "multi_seat_sofa", "dining_table", "desk")):
        primary = next(k for k in ("sofa", "multi_seat_sofa", "dining_table", "desk") if k in counts)
    relations = []
    if primary:
        for category in counts:
            if category != primary and category in {"nightstand", "chair", "dining_chair", "coffee_table", "tv_stand"}:
                relations.append({"subject": category, "predicate": "near", "object": primary, "source": "rule"})
    constraints = ["inside_room", "avoid_overlap", "palette_exact", "use_architecture_condition_image"]
    if has_door:
        constraints.append("door_clearance_free")
    if has_window:
        constraints.append("window_clearance_free")
    return {
        "schema_version": "scene-facts-v1",
        "sample_id": sample_id or layout.get("sample_id") or architecture.get("architecture_id"),
        "room_type": room_type,
        "room_type_source": source,
        "furniture_counts": dict(sorted(counts.items())),
        "primary_anchor": primary,
        "architecture_facts": {
            "has_door": has_door,
            "has_window": has_window,
            "metric_transform_exists": isinstance(architecture.get("metric_transform"), dict),
            "renderer_version": "metric_v2" if isinstance(architecture.get("metric_transform"), dict) else "normalized_v1",
        },
        "relation_facts": relations,
        "global_constraints": constraints,
    }
