
from __future__ import annotations

import math
from collections import Counter
from typing import Any

ANCHOR_PRIORITY = [
    "double_bed", "single_bed", "bed", "dining_table", "multi_seat_sofa", "sofa",
    "desk", "wardrobe", "coffee_table", "tv_stand", "cabinet", "dressing_table",
]


def _center(obj: dict[str, Any]) -> tuple[float, float] | None:
    c = obj.get("center_m")
    if isinstance(c, list) and len(c) >= 2:
        return float(c[0]), float(c[1])
    return None


def _anchor_category(objects: list[dict[str, Any]], scene_facts: dict[str, Any] | None = None) -> str | None:
    if scene_facts and scene_facts.get("primary_anchor"):
        return scene_facts["primary_anchor"]
    cats = Counter(o.get("category") for o in objects if o.get("category"))
    for cat in ANCHOR_PRIORITY:
        if cats.get(cat):
            return cat
    return next(iter(cats), None)


def extract_relation_triplets(
    layout_json: dict[str, Any],
    architecture_json: dict[str, Any] | None = None,
    goal_lostate_rich: dict[str, Any] | None = None,
    scene_facts: dict[str, Any] | None = None,
    max_triplets: int = 5,
) -> list[dict[str, Any]]:
    objects = [o for o in layout_json.get("objects", []) if o.get("category") and _center(o)]
    if len(objects) < 2:
        return []
    pairs: list[tuple[float, dict[str, Any]]] = []
    for i, a in enumerate(objects):
        ca = _center(a)
        for b in objects[i + 1:]:
            cb = _center(b)
            if ca is None or cb is None:
                continue
            dx, dz = cb[0] - ca[0], cb[1] - ca[1]
            dist = math.hypot(dx, dz)
            if dist > 3.2:
                continue
            pred = "closely_near" if dist <= 1.2 else "near"
            pairs.append((dist, {
                "subject": a["category"], "predicate": pred, "object": b["category"],
                "confidence": round(max(0.55, min(0.98, 1.0 - dist / 4.0)), 3), "source": "layout_distance_rule",
            }))
            if abs(dx) > abs(dz) * 1.35:
                pred2 = "left_of" if dx > 0 else "right_of"
            elif abs(dz) > abs(dx) * 1.35:
                pred2 = "in_front_of" if dz > 0 else "behind"
            else:
                pred2 = None
            if pred2:
                pairs.append((dist + 0.05, {
                    "subject": a["category"], "predicate": pred2, "object": b["category"],
                    "confidence": round(max(0.55, min(0.9, 1.0 - dist / 5.0)), 3), "source": "layout_direction_rule",
                }))
    anchor = _anchor_category(objects, scene_facts)
    if anchor:
        for cat, count in Counter(o.get("category") for o in objects).items():
            if cat and cat != anchor and count >= 1:
                pairs.append((0.0, {
                    "subject": cat, "predicate": "main_anchor_of" if cat == anchor else "paired_with",
                    "object": anchor, "confidence": 0.8, "source": "goal_anchor_rule",
                }))
    if architecture_json:
        arch = architecture_json
        has_door = bool(arch.get("doors") or arch.get("door_regions") or arch.get("clearance_regions"))
        has_window = bool(arch.get("windows") or arch.get("window_regions"))
        if has_door and anchor:
            pairs.append((0.1, {"subject": anchor, "predicate": "away_from_door_clearance", "object": "door_clearance", "confidence": 0.75, "source": "architecture_clearance_rule"}))
        if has_window and anchor:
            pairs.append((0.2, {"subject": anchor, "predicate": "away_from_window_clearance", "object": "window_clearance", "confidence": 0.72, "source": "architecture_clearance_rule"}))
    seen = set()
    out = []
    for _, rel in sorted(pairs, key=lambda x: (x[0], -x[1].get("confidence", 0))):
        key = (rel["subject"], rel["predicate"], rel["object"])
        if key in seen or rel["subject"] == rel["object"]:
            continue
        seen.add(key)
        out.append(rel)
        if len(out) >= max_triplets:
            break
    return out
