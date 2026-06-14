#!/usr/bin/env python
"""Rule-based Prompt Compiler for LoReflection generation prompts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_NEGATIVE = "photorealistic texture, perspective view, shadows, labels, text, clutter, cropped room"
DEFAULT_STYLE = ["top-down orthographic semantic map", "fixed-palette semantic map", "clean object boundaries"]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def architecture_constraints(architecture: dict) -> list[str]:
    constraints = []
    boundary = architecture.get("boundary", {}).get("polygon_m", [])
    if boundary:
        constraints.append(f"Keep all furniture inside the room boundary with {len(boundary)} vertices.")
    for anchor in architecture.get("anchors", []):
        anchor_id = anchor.get("anchor_id", "unknown_anchor")
        anchor_type = anchor.get("anchor_type", "anchor")
        constraints.append(f"Respect architectural {anchor_type} {anchor_id}.")
    return constraints


def compile_prompt_package(goal_lostate: dict, architecture: dict, architecture_image: str | None = None) -> dict:
    """Compile Goal LoState and Architecture JSON into a generation prompt package."""
    task_id = goal_lostate.get("metadata", {}).get("task_id", "unknown_task")
    room_type = goal_lostate.get("room_type", architecture.get("room_type", "room"))
    object_checklist = []
    object_phrases = []
    for slot in goal_lostate.get("furniture_slots", []):
        count = slot.get("count", 1)
        category = slot.get("category", "object")
        necessity = "required" if slot.get("required", True) else "optional"
        object_checklist.append(f"{slot.get('slot_id')}: {count} {category} ({necessity})")
        if slot.get("required", True):
            object_phrases.append(f"{count} required {category}")

    relation_checklist = []
    required_relation_phrases = []
    preferred_relation_phrases = []
    for rel in goal_lostate.get("desired_relations", []):
        subject = rel.get("subject", "subject")
        predicate = rel.get("predicate", "related_to")
        obj = rel.get("object", "object")
        necessity = rel.get("necessity", "required")
        relation_checklist.append(f"{subject} {predicate} {obj} ({necessity})")
        phrase = f"{subject} {predicate} {obj}"
        if necessity == "required":
            required_relation_phrases.append(phrase)
        else:
            preferred_relation_phrases.append(phrase)

    positive_parts = [
        f"A top-down fixed-palette semantic {room_type} layout.",
        "Include " + ", ".join(object_phrases) + "." if object_phrases else "Use the requested furniture set.",
    ]
    if required_relation_phrases:
        positive_parts.append("Required layout relations: " + "; ".join(required_relation_phrases) + ".")
    if preferred_relation_phrases:
        positive_parts.append("Preferred layout relations when feasible: " + "; ".join(preferred_relation_phrases) + ".")
    positive_parts.append("Respect walls, doors, windows, boundaries, and clearance regions.")
    positive_parts.append("Use a top-down orthographic fixed-palette semantic map style with clean object boundaries.")

    package = {
        "schema_version": "prompt-package-v1",
        "task_id": task_id,
        "architecture_id": architecture.get("architecture_id"),
        "architecture_image": architecture_image,
        "positive_prompt": " ".join(positive_parts),
        "negative_prompt": DEFAULT_NEGATIVE,
        "object_checklist": object_checklist,
        "relation_checklist": relation_checklist,
        "architecture_constraints": architecture_constraints(architecture),
        "style_constraints": DEFAULT_STYLE,
    }
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-lostate", required=True, type=Path, help="Input Goal LoState JSON.")
    parser.add_argument("--architecture", required=True, type=Path, help="Input Architecture JSON.")
    parser.add_argument("--architecture-image", default=None, help="Optional architecture condition image path.")
    parser.add_argument("--output", required=True, type=Path, help="Output Prompt Package JSON.")
    args = parser.parse_args()

    package = compile_prompt_package(load_json(args.goal_lostate), load_json(args.architecture), args.architecture_image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote prompt package to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
