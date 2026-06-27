from __future__ import annotations

from pathlib import Path
from typing import Any

from .palette_contract import (
    build_palette_control_prompt,
    get_active_palette_entries,
    load_palette_contract,
    validate_active_palette_entries,
)


ARCHITECTURE_CONTROL_PROMPT = (
    "Architecture_Control. Use the architecture condition image for the room floor region, room boundary, and doors/windows when visible. Keep all furniture inside floor pixels and avoid door/window areas."
)


def _required_counts(goal_lostate: dict[str, Any]) -> dict[str, Any]:
    if isinstance(goal_lostate.get("required_counts"), dict):
        return goal_lostate["required_counts"]
    counts: dict[str, int] = {}
    for slot in goal_lostate.get("furniture_slots", []):
        if not isinstance(slot, dict):
            continue
        category = slot.get("category") or slot.get("semantic_category")
        count = slot.get("count") or slot.get("required_count") or 1
        if category:
            counts[str(category)] = counts.get(str(category), 0) + int(count)
    return counts


def compile_prompt_package_v2(
    user_intent_prompt: str,
    goal_lostate: dict[str, Any],
    prompt_package: dict[str, Any],
    c2rgb_path: str | Path,
    id2c_path: str | Path | None = None,
    include_rgb: bool = False,
    source_prompt_package: str | None = None,
    goal_lostate_ref: str | None = None,
) -> dict[str, Any]:
    contract = load_palette_contract(c2rgb_path, id2c_path)
    required_counts = _required_counts(goal_lostate)
    active_entries = get_active_palette_entries(required_counts, contract["c2rgb"])
    active_categories = sorted(active_entries)
    validation = validate_active_palette_entries(active_categories, contract["c2rgb"])
    palette_control = build_palette_control_prompt(active_categories, include_rgb=include_rgb)
    prompt = "\n\n".join([user_intent_prompt.strip(), ARCHITECTURE_CONTROL_PROMPT, palette_control]).strip()
    notes = []
    if not validation["valid"]:
        notes.append({"type": "active_palette_validation", "details": validation})
    return {
        "schema_version": "prompt-package-v2-palette-contract",
        "user_intent_prompt": user_intent_prompt,
        "architecture_control_prompt": ARCHITECTURE_CONTROL_PROMPT,
        "palette_control_prompt": palette_control,
        "compiled_prompt": prompt,
        "compiled_text_prompt": prompt,
        "palette_contract_ref": Path(c2rgb_path).as_posix(),
        "active_palette_entries": active_entries,
        "active_palette_categories": active_categories,
        "source_prompt_package": source_prompt_package,
        "goal_lostate_ref": goal_lostate_ref,
        "source_prompt_schema_version": prompt_package.get("schema_version"),
        "geometry_verified_constraints": prompt_package.get("geometry_verified_constraints", []),
        "dropped_constraints": prompt_package.get("dropped_constraints", []),
        "notes": notes,
    }
