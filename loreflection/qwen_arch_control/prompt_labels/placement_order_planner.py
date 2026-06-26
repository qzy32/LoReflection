
from __future__ import annotations
from collections import Counter
from typing import Any

ANCHORS = ["double_bed", "single_bed", "bed", "dining_table", "multi_seat_sofa", "sofa", "desk", "wardrobe", "coffee_table"]
SMALL = {"nightstand", "chair", "dining_chair", "stool", "ceiling_lamp", "lamp", "side_table"}


def plan_placement_order(scene_facts: dict[str, Any], goal_lostate_rich: dict[str, Any] | None = None, relation_triplets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    counts = scene_facts.get("furniture_counts") or (goal_lostate_rich or {}).get("required_counts") or {}
    cats = list(counts.keys())
    primary = scene_facts.get("primary_anchor") or next((c for c in ANCHORS if c in counts), cats[0] if cats else "furniture")
    main = [primary]
    supporting = [c for c in cats if c not in main and c not in SMALL]
    small = [c for c in cats if c in SMALL and c not in main]
    rel_bits = []
    for rel in (relation_triplets or [])[:3]:
        rel_bits.append(f"keep {rel.get('subject')} {rel.get('predicate')} {rel.get('object')}")
    summary = f"Place the {primary} as the main anchor"
    if supporting:
        summary += ", then arrange " + ", ".join(supporting)
    if small:
        summary += ", then add " + ", ".join(small)
    if rel_bits:
        summary += "; " + "; ".join(rel_bits)
    summary += "."
    return {"main_anchors": main, "supporting_furniture": supporting, "small_or_decorative": small, "placement_order_summary": summary}
