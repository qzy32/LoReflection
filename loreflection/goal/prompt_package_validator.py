"""Strict validation for LLM Functional PromptPackage output."""

from __future__ import annotations

import re
from typing import Any

NEGATIVE_PROMPT = "photorealistic texture, perspective view, shadows, labels, text, clutter, cropped room"

ERROR_JSON_INVALID = "LLM_PROMPT_JSON_INVALID"
ERROR_SCHEMA_INVALID = "LLM_PROMPT_SCHEMA_INVALID"
ERROR_GEOMETRY_LEAKAGE = "LLM_PROMPT_GEOMETRY_LEAKAGE"
ERROR_UNKNOWN_CATEGORY = "LLM_PROMPT_UNKNOWN_CATEGORY"
ERROR_INVALID_ARCHITECTURE_CLAIM = "LLM_PROMPT_INVALID_ARCHITECTURE_CLAIM"
ERROR_EMPTY = "LLM_PROMPT_EMPTY"
ERROR_TOO_LONG = "LLM_PROMPT_TOO_LONG"
ERROR_CLIENT_MISSING = "LLM_PROMPT_CLIENT_MISSING"
ERROR_NON_ENGLISH = "LLM_PROMPT_NON_ENGLISH"
ERROR_LAYOUT_JSON = "LLM_PROMPT_LAYOUT_JSON_LEAKAGE"

GEOMETRY_LEAKAGE_PATTERNS = [
    r"\bcenter_m\b", r"\bsize_m\b", r"\borientation_deg\b", r"\bbbox\b", r"\bfootprint\b",
    r"\bpixel\b", r"\bpx\b", r"\bcm\b", r"\bmeter\b", r"\bcoordinate\b", r"\bsource_json_path\b", r"\buid\b",
]
GEOMETRY_LEAKAGE_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in GEOMETRY_LEAKAGE_PATTERNS]
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

CLAIM_MAP = {
    "room_floor_boundary": "room_floor_boundary",
    "visible_door": "door",
    "door": "door",
    "visible_window": "window",
    "window": "window",
    "visible_wall": "wall_class",
    "wall": "wall_class",
    "visible_clearance_region": "clearance_region",
    "clearance_region": "clearance_region",
    "visible_non_placeable_region": "non_placeable_region",
    "non_placeable_region": "non_placeable_region",
}


class PromptCompilerError(RuntimeError):
    def __init__(self, code: str, details: Any | None = None):
        self.code = code
        self.details = details
        super().__init__(code if details is None else f"{code}: {details}")


def registry_palette(registry: Any | None) -> dict[str, Any]:
    if registry is None:
        return {}
    for attr in ("name_to_rgb", "palette", "colors"):
        value = getattr(registry, attr, None)
        if isinstance(value, dict):
            return value
    if isinstance(registry, dict):
        colors = registry.get("colors")
        if isinstance(colors, dict):
            return colors
        return registry
    return {}


def active_categories(goal_lostate: dict[str, Any]) -> list[str]:
    counts = goal_lostate.get("required_counts") or {}
    cats = {str(k) for k, v in counts.items() if int(v or 0) > 0}
    for slot in goal_lostate.get("furniture_slots", []) or []:
        if isinstance(slot, dict) and slot.get("category"):
            cats.add(str(slot["category"]))
    return sorted(cats)


def active_palette_entries(goal_lostate: dict[str, Any], registry: Any | None) -> dict[str, list[int]]:
    palette = registry_palette(registry)
    out: dict[str, list[int]] = {}
    for cat in active_categories(goal_lostate):
        if cat in palette:
            out[cat] = [int(v) for v in palette[cat]]
    return out


def allowed_slot_ids(goal_lostate: dict[str, Any]) -> set[str]:
    return {str(slot.get("slot_id")) for slot in goal_lostate.get("furniture_slots", []) if isinstance(slot, dict) and slot.get("slot_id")}


def allowed_constraint_ids(goal_lostate: dict[str, Any]) -> set[str]:
    return {str(c.get("constraint_id")) for c in goal_lostate.get("goal_constraints", []) if isinstance(c, dict) and c.get("constraint_id")}


def validate_prompt_package(package: dict[str, Any], goal_lostate: dict[str, Any], architecture_summary: dict[str, Any], registry: Any | None = None) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    prompt = str(package.get("compiled_text_prompt") or "").strip()
    if not prompt:
        errors.append({"code": ERROR_EMPTY})
    words = re.findall(r"\S+", prompt)
    if len(words) > 120:
        errors.append({"code": ERROR_TOO_LONG, "word_count": len(words)})
    if CJK_RE.search(prompt):
        errors.append({"code": ERROR_NON_ENGLISH})
    leakage = [pattern for pattern, regex in zip(GEOMETRY_LEAKAGE_PATTERNS, GEOMETRY_LEAKAGE_REGEX) if regex.search(prompt)]
    if leakage:
        errors.append({"code": ERROR_GEOMETRY_LEAKAGE, "patterns": leakage})
    if "layout_json" in prompt or "scene_json" in prompt or "StatePatch" in prompt or "{" in prompt:
        errors.append({"code": ERROR_LAYOUT_JSON})

    slots = set(map(str, package.get("used_slot_ids") or []))
    slot_allowed = allowed_slot_ids(goal_lostate)
    if slots - slot_allowed:
        errors.append({"code": ERROR_SCHEMA_INVALID, "field": "used_slot_ids", "unknown": sorted(slots - slot_allowed)})

    constraint_ids = set(map(str, (package.get("used_constraint_ids") or []) + (package.get("omitted_constraint_ids") or [])))
    constraint_allowed = allowed_constraint_ids(goal_lostate)
    if constraint_ids - constraint_allowed:
        errors.append({"code": ERROR_SCHEMA_INVALID, "field": "constraint_ids", "unknown": sorted(constraint_ids - constraint_allowed)})

    palette = registry_palette(registry)
    allowed_categories = {str(k) for k in palette if k not in {"void", "floor", "door", "window"}}
    allowed_categories.update(active_categories(goal_lostate))
    for token in re.findall(r"\b[a-z]+(?:_[a-z]+)+\b", prompt):
        if token not in allowed_categories and token not in {"top_down", "fixed_palette"}:
            errors.append({"code": ERROR_UNKNOWN_CATEGORY, "category": token})
            break

    visible = (architecture_summary or {}).get("visible_architecture_elements", {})
    invalid_claims = []
    for claim in map(str, package.get("architecture_claims") or []):
        key = CLAIM_MAP.get(claim)
        if key is None or not visible.get(key):
            invalid_claims.append(claim)
    if invalid_claims:
        errors.append({"code": ERROR_INVALID_ARCHITECTURE_CLAIM, "claims": invalid_claims})

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "geometry_leakage": leakage,
        "unknown_categories": [e.get("category") for e in errors if e.get("code") == ERROR_UNKNOWN_CATEGORY],
        "invalid_architecture_claims": invalid_claims,
    }


def raise_if_invalid(report: dict[str, Any]) -> None:
    if report.get("status") == "pass":
        return
    first = (report.get("errors") or [{}])[0]
    raise PromptCompilerError(str(first.get("code") or ERROR_SCHEMA_INVALID), report)
