"""Prompt Compiler for Qwen-Image Architecture In-Context Control."""

from __future__ import annotations

import re
from typing import Any


NEGATIVE_PROMPT = "photorealistic texture, perspective view, shadows, labels, text, clutter, cropped room"
LEAKAGE_PATTERNS = [
    r"\bcenter_m\b",
    r"\bsize_m\b",
    r"\borientation_deg\b",
    r"\bbbox\b",
    r"\bfootprint\b",
    r"\bpixel\b",
    r"\bpx\b",
    r"\bcm\b",
    r"\bmeter\b",
    r"\bCSS\b",
    r"\bcoordinate\b",
    r"\bsource_json_path\b",
]
LEAKAGE_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in LEAKAGE_PATTERNS]


def _safe_text(value: Any) -> str:
    text = str(value or "").strip()
    if any(regex.search(text) for regex in LEAKAGE_REGEX):
        return ""
    return text


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


def compile_prompt_package(goal_lostate: dict[str, Any]) -> dict[str, Any]:
    """Compile Goal LoState v2 into a geometry-safe Qwen text prompt package.

    The v8 contract passes architecture through an architecture condition image,
    so this compiler only consumes Goal LoState.
    """

    task_id = goal_lostate.get("metadata", {}).get("task_id", "unknown_task")
    room_type = _safe_text(goal_lostate.get("room_type")) or "room"
    slots = [slot for slot in goal_lostate.get("furniture_slots", []) if isinstance(slot, dict)]
    constraints = [c for c in goal_lostate.get("goal_constraints", []) if isinstance(c, dict)]
    policy = goal_lostate.get("prompt_compilation_policy") or {}
    include_optional_slots = bool(policy.get("include_optional_slots", True))
    include_preferred_constraints = bool(policy.get("include_preferred_constraints", True))

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

    parts = [
        f"Context_Control. Create a top-down fixed-palette semantic {room_type} layout.",
        "Use the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions.",
    ]
    if required_slots:
        parts.append("Required furniture: " + ", ".join(required_slots) + ".")
    if optional_slots:
        parts.append("Optional furniture when feasible: " + ", ".join(optional_slots) + ".")
    if prompt_hints:
        parts.append("Layout guidance: " + " ".join(prompt_hints))
    parts.append("Keep all architectural clearance and non-placeable regions free.")
    parts.append("Use only frozen semantic categories and the frozen palette.")

    compiled_text_prompt = " ".join(parts)
    leaked = [pattern for pattern, regex in zip(LEAKAGE_PATTERNS, LEAKAGE_REGEX) if regex.search(compiled_text_prompt)]
    if leaked:
        raise ValueError(f"compiled prompt contains geometry leakage: {leaked}")

    return {
        "schema_version": "prompt-package-v2",
        "task_id": task_id,
        "compiled_text_prompt": compiled_text_prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "prompt_constraint_refs": prompt_constraint_refs,
        "verifier_only_constraint_refs": verifier_only_constraint_refs,
        "constraint_routes": constraint_routes,
    }
