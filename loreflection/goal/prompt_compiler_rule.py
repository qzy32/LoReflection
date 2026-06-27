"""Rule-based Prompt Compiler fallback for Qwen architecture control."""

from __future__ import annotations

import re
from typing import Any

NEGATIVE_PROMPT = "photorealistic texture, perspective view, shadows, labels, text, clutter, cropped room"
LEAKAGE_PATTERNS = [
    r"\bcenter_m\b", r"\bsize_m\b", r"\borientation_deg\b", r"\bbbox\b", r"\bfootprint\b",
    r"\bpixel\b", r"\bpx\b", r"\bcm\b", r"\bmeter\b", r"\bCSS\b", r"\bcoordinate\b", r"\bsource_json_path\b",
]
LEAKAGE_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in LEAKAGE_PATTERNS]


def _safe_text(value: Any) -> str:
    text = str(value or "").strip()
    if any(regex.search(text) for regex in LEAKAGE_REGEX):
        return ""
    return text


def _active_categories(goal_lostate: dict[str, Any]) -> list[str]:
    counts = goal_lostate.get("required_counts") or {}
    cats = set(str(k) for k in counts if k)
    for slot in goal_lostate.get("furniture_slots", []) or []:
        if isinstance(slot, dict) and slot.get("category"):
            cats.add(str(slot["category"]))
    return sorted(cats)


def _palette_entries(categories: list[str], registry: Any | None) -> dict[str, list[int]]:
    palette = getattr(registry, "palette", None) if registry is not None else None
    if not isinstance(palette, dict):
        palette = getattr(registry, "colors", None) if registry is not None else None
    if not isinstance(palette, dict):
        return {}
    return {cat: list(palette[cat]) for cat in categories if cat in palette}


def _palette_mapping_text(categories: list[str], entries: dict[str, list[int]]) -> str:
    parts = []
    for category in categories:
        rgb = entries.get(category)
        if rgb and len(rgb) == 3:
            parts.append(f"{category}=({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})")
        else:
            parts.append(category)
    return ", ".join(parts) if parts else "none"


def _slot_phrase(slot: dict[str, Any]) -> str:
    count = int(slot.get("count", 1) or 1)
    category = _safe_text(slot.get("category")) or "object"
    role = _safe_text(slot.get("role"))
    required = "required" if slot.get("required", True) else "optional"
    if role:
        return f"{count} {required} {category} for {role}"
    return f"{count} {required} {category}"


def _constraint_route(constraint: dict[str, Any]) -> tuple[str, str]:
    cid = str(constraint.get("constraint_id", "constraint"))
    necessity = constraint.get("necessity", "required")
    hint = _safe_text(constraint.get("prompt_hint"))
    verification = constraint.get("verification") or {}
    if necessity == "required" and hint:
        return cid, "prompt"
    if verification:
        return cid, "verifier_only"
    return cid, "prompt" if hint else "verifier_only"


def _architecture_control_text(architecture_summary: dict[str, Any] | None = None) -> str:
    visible = (architecture_summary or {}).get("visible_architecture_elements", {})
    parts = ["Use the architecture condition image for the room floor boundary"]
    if visible.get("door"):
        parts.append("visible doors")
    if visible.get("window"):
        parts.append("visible windows")
    return "Architecture_Control. " + ", ".join(parts) + ". Keep all furniture inside floor pixels and avoid door/window areas."


def compile_prompt_package_rule(goal_lostate: dict[str, Any], architecture_summary: dict[str, Any] | None = None, registry: Any | None = None) -> dict[str, Any]:
    task_id = goal_lostate.get("metadata", {}).get("task_id", "unknown_task")
    room_type = _safe_text(goal_lostate.get("room_type")) or "room"
    slots = [slot for slot in goal_lostate.get("furniture_slots", []) if isinstance(slot, dict)]
    constraints = [c for c in goal_lostate.get("goal_constraints", []) if isinstance(c, dict)]
    policy = goal_lostate.get("prompt_compilation_policy") or {}
    include_optional_slots = bool(policy.get("include_optional_slots", True))
    include_preferred_constraints = bool(policy.get("include_preferred_constraints", True))
    active_categories = _active_categories(goal_lostate)
    active_palette_entries = _palette_entries(active_categories, registry)

    slot_phrases = [_slot_phrase(slot) for slot in slots]
    required_slots = [phrase for phrase in slot_phrases if "required" in phrase]
    optional_slots = [phrase for phrase in slot_phrases if "optional" in phrase] if include_optional_slots else []
    constraint_routes = dict(_constraint_route(c) for c in constraints)
    if not include_preferred_constraints:
        for constraint in constraints:
            if constraint.get("necessity") == "preferred":
                constraint_routes[str(constraint.get("constraint_id", "constraint"))] = "verifier_only"
    prompt_constraint_refs = [cid for cid, route in constraint_routes.items() if route == "prompt"]
    verifier_only_constraint_refs = [cid for cid, route in constraint_routes.items() if route == "verifier_only"]
    prompt_hints = [_safe_text(c.get("prompt_hint")) for c in constraints if constraint_routes.get(str(c.get("constraint_id", "constraint"))) == "prompt"]
    prompt_hints = [hint for hint in prompt_hints if hint]

    parts = [f"Context_Control. Create a top-down fixed-palette semantic {room_type} layout.", _architecture_control_text(architecture_summary)]
    if required_slots:
        parts.append("Required furniture: " + ", ".join(required_slots) + ".")
    if optional_slots:
        parts.append("Optional furniture when feasible: " + ", ".join(optional_slots) + ".")
    if prompt_hints:
        parts.append("Layout guidance: " + " ".join(prompt_hints))
    active_text = _palette_mapping_text(active_categories, active_palette_entries)
    parts.append("Palette_Control. Generate a fixed-palette semantic layout only. Use the frozen category-to-color semantic palette. Draw each active furniture category with its assigned RGB palette color only. Active semantic category palette entries: " + active_text + ".")
    compiled_text_prompt = " ".join(parts)
    leaked = [pattern for pattern, regex in zip(LEAKAGE_PATTERNS, LEAKAGE_REGEX) if regex.search(compiled_text_prompt)]
    if leaked:
        raise ValueError(f"compiled prompt contains geometry leakage: {leaked}")
    return {
        "schema_version": "prompt-package-v3",
        "task_id": task_id,
        "prompt_compiler_mode": "rule",
        "compiled_text_prompt": compiled_text_prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "active_palette_categories": active_categories,
        "active_palette_entries": active_palette_entries,
        "prompt_constraint_refs": prompt_constraint_refs,
        "verifier_only_constraint_refs": verifier_only_constraint_refs,
        "constraint_routes": constraint_routes,
        "llm_prompt_compiler_report": {"used_llm": False, "fallback_used": False, "validation_status": "not_applicable"},
    }


compile_prompt_package = compile_prompt_package_rule
