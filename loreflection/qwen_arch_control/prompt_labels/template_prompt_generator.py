from __future__ import annotations

from typing import Any


def _count_phrase(category: str, count: int) -> str:
    name = category.replace("_", " ")
    return f"{count} {name}" if count == 1 else f"{count} {name}s"


def _items(counts: dict[str, int]) -> str:
    phrases = [_count_phrase(k, int(v)) for k, v in counts.items()]
    if not phrases:
        return "the required furniture"
    if len(phrases) == 1:
        return phrases[0]
    return ", ".join(phrases[:-1]) + ", and " + phrases[-1]


def generate_prompt_variants(scene_facts: dict[str, Any]) -> dict[str, str]:
    room = str(scene_facts.get("room_type") or "room").replace("_", " ")
    counts = scene_facts.get("furniture_counts", {})
    items = _items(counts)
    primary = str(scene_facts.get("primary_anchor") or "main furniture").replace("_", " ")
    return {
        "template_minimal": f"Context_Control. Create a top-down fixed-palette semantic {room} layout with {items}. Follow the architecture condition image, keep furniture inside the room, and keep door and window clearance regions free.",
        "template_functional": f"Context_Control. Design a functional {room} semantic layout with {items}. Use the {primary} as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.",
        "template_user_like": f"Context_Control. I need a practical {room} layout with {items}. Respect the room shape shown in the architecture image and avoid blocking doors or windows.",
    }


def prompt_package(variant_name: str, prompt: str, scene_facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "prompt-package-v2-template",
        "variant_name": variant_name,
        "compiled_text_prompt": prompt,
        "negative_prompt": "coordinates, pixel values, metric dimensions, hidden ids, source paths",
        "prompt_constraint_refs": scene_facts.get("global_constraints", []),
        "verifier_only_constraint_refs": [],
        "constraint_routes": {name: "prompt" for name in scene_facts.get("global_constraints", [])},
    }
