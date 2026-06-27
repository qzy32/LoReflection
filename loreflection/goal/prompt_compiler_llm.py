"""Constrained LLM Prompt Compiler for Goal LoState verbalization."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from .prompt_compiler_rule import LEAKAGE_REGEX, NEGATIVE_PROMPT, _active_categories, _palette_entries, _registry_palette, compile_prompt_package_rule

SYSTEM_PROMPT = """You are a prompt compiler for fixed-palette semantic top-down indoor layout generation.
Your job is to verbalize a symbolic Goal LoState into a concise Context_Control user intent for Qwen-Image Architecture In-Context Control.
Do not invent furniture categories.
Do not invent doors, windows, walls, clearance regions, or non-placeable regions.
Only mention architecture elements listed as visible in architecture_summary.
Do not include coordinates, dimensions, pixels, bounding boxes, metric units, JSON paths, or object ids.
Do not output layout JSON.
Do not output furniture positions.
Output only valid JSON with user_intent_prompt, used_slot_ids, used_constraint_ids, omitted_constraint_ids, architecture_claims, notes.
The program will append Architecture_Control and Palette_Control with exact RGB palette entries."""

WORD_SPLIT = re.compile(r"\s+")


class PromptLLMClient(Protocol):
    def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any] | str:
        ...


def build_architecture_summary(architecture: dict[str, Any] | None = None) -> dict[str, Any]:
    architecture = architecture or {}
    door_count = int(architecture.get("door_anchor_count") or architecture.get("native_room_child_door_count") or 0)
    window_count = int(architecture.get("window_anchor_count") or architecture.get("native_room_child_window_count") or 0)
    return {
        "room_type": architecture.get("room_type"),
        "visible_architecture_elements": {
            "room_floor_boundary": True,
            "door": door_count > 0,
            "window": window_count > 0,
            "wall_class": False,
            "clearance_region": False,
            "non_placeable_region": False,
        },
        "opening_source_policy": architecture.get("opening_source_policy", "semlayoutdiff_room_children_only"),
        "qwen_input_is_palette_exact": True,
    }


def _allowed_categories(goal_lostate: dict[str, Any], registry: Any | None = None) -> set[str]:
    cats = set(_active_categories(goal_lostate))
    palette = _registry_palette(registry)
    cats.update(str(k) for k in palette if k not in {"void", "floor", "door", "window"})
    return cats


def _slot_ids(goal_lostate: dict[str, Any]) -> set[str]:
    return {str(slot.get("slot_id")) for slot in goal_lostate.get("furniture_slots", []) if isinstance(slot, dict) and slot.get("slot_id")}


def _constraint_ids(goal_lostate: dict[str, Any]) -> set[str]:
    return {str(c.get("constraint_id")) for c in goal_lostate.get("goal_constraints", []) if isinstance(c, dict) and c.get("constraint_id")}


def _palette_mapping_text(categories: list[str], entries: dict[str, list[int]]) -> str:
    parts = []
    for category in categories:
        rgb = entries.get(category)
        if rgb and len(rgb) == 3:
            parts.append(f"{category}=({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})")
        else:
            parts.append(category)
    return ", ".join(parts) if parts else "none"


def _architecture_control_text(architecture_summary: dict[str, Any]) -> str:
    visible = architecture_summary.get("visible_architecture_elements", {})
    parts = ["Use the architecture condition image for the room floor boundary"]
    if visible.get("door"):
        parts.append("visible doors")
    if visible.get("window"):
        parts.append("visible windows")
    return "Architecture_Control. " + ", ".join(parts) + ". Keep all furniture inside floor pixels and avoid door/window areas."


def _palette_control_text(goal_lostate: dict[str, Any], registry: Any | None) -> tuple[str, list[str], dict[str, list[int]]]:
    active = _active_categories(goal_lostate)
    entries = _palette_entries(active, registry)
    mapping = _palette_mapping_text(active, entries)
    text = "Palette_Control. Generate a fixed-palette semantic layout only. Use the frozen category-to-color semantic palette. Draw each active furniture category with its assigned RGB palette color only. Active semantic category palette entries: " + mapping + "."
    return text, active, entries


def _safe_goal_payload(goal_lostate: dict[str, Any], architecture_summary: dict[str, Any], registry: Any | None) -> dict[str, Any]:
    active_categories = _active_categories(goal_lostate)
    active_palette_entries = _palette_entries(active_categories, registry)
    slots = []
    for slot in goal_lostate.get("furniture_slots", []) or []:
        if isinstance(slot, dict):
            slots.append({k: slot.get(k) for k in ("slot_id", "category", "count", "required", "role") if k in slot})
    constraints = []
    for c in goal_lostate.get("goal_constraints", []) or []:
        if isinstance(c, dict):
            constraints.append({k: c.get(k) for k in ("constraint_id", "constraint_kind", "necessity", "prompt_hint", "intent_tag") if k in c})
    return {
        "room_type": goal_lostate.get("room_type"),
        "furniture_slots": slots,
        "goal_constraints": constraints,
        "prompt_compilation_policy": goal_lostate.get("prompt_compilation_policy") or {},
        "allowed_furniture_categories": sorted(_allowed_categories(goal_lostate, registry)),
        "active_palette_categories": active_categories,
        "active_palette_entries": active_palette_entries,
        "architecture_summary": architecture_summary,
        "output_schema": {
            "user_intent_prompt": "Context_Control sentence or short paragraph only",
            "used_slot_ids": ["slot ids from furniture_slots"],
            "used_constraint_ids": ["constraint ids from goal_constraints"],
            "omitted_constraint_ids": ["constraint ids from goal_constraints"],
            "architecture_claims": ["room_floor_boundary", "visible_door", "visible_window"],
            "notes": [],
        },
    }


def _parse_llm_output(raw: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    text = str(raw).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def _compiled_from_output(output: dict[str, Any], goal_lostate: dict[str, Any], architecture_summary: dict[str, Any], registry: Any | None) -> tuple[str, list[str], dict[str, list[int]]]:
    intent = str(output.get("user_intent_prompt") or output.get("compiled_text_prompt") or "").strip()
    if not intent.startswith("Context_Control."):
        intent = "Context_Control. " + intent.removeprefix("Context_Control").lstrip(". ")
    arch_text = _architecture_control_text(architecture_summary)
    palette_text, active, entries = _palette_control_text(goal_lostate, registry)
    return "\n\n".join([intent, arch_text, palette_text]), active, entries


def validate_llm_prompt_output(output: dict[str, Any], goal_lostate: dict[str, Any], architecture_summary: dict[str, Any], registry: Any | None = None) -> tuple[list[str], str, list[str], dict[str, list[int]]]:
    errors: list[str] = []
    prompt, active, active_entries = _compiled_from_output(output, goal_lostate, architecture_summary, registry)
    if not prompt.strip():
        errors.append("compiled_text_prompt_missing")
    if len(WORD_SPLIT.findall(prompt.strip())) > 160:
        errors.append("compiled_text_prompt_too_long")
    if any(regex.search(prompt) for regex in LEAKAGE_REGEX):
        errors.append("geometry_leakage")
    if "{" in prompt or "layout_json" in prompt or "scene_json" in prompt:
        errors.append("layout_json_leakage")
    for section in ["Context_Control.", "Architecture_Control.", "Palette_Control."]:
        if section not in prompt:
            errors.append(f"missing_{section.split('.')[0].lower()}")
    if not all(category in prompt for category in active):
        errors.append("active_category_missing_from_prompt")
    normalized_prompt = prompt.replace(" ", "")
    for category, rgb in active_entries.items():
        rgb_text = f"{category}=({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
        if rgb_text not in normalized_prompt:
            errors.append("active_palette_rgb_missing_from_prompt")
            break
    allowed_slots = _slot_ids(goal_lostate)
    used_slots = set(map(str, output.get("used_slot_ids") or []))
    if used_slots - allowed_slots:
        errors.append("unknown_slot_id")
    allowed_constraints = _constraint_ids(goal_lostate)
    used_constraints = set(map(str, output.get("used_constraint_ids") or []))
    omitted_constraints = set(map(str, output.get("omitted_constraint_ids") or []))
    if (used_constraints | omitted_constraints) - allowed_constraints:
        errors.append("unknown_constraint_id")
    allowed_categories = _allowed_categories(goal_lostate, registry)
    for token in re.findall(r"\b[a-z]+(?:_[a-z]+)+\b", prompt):
        if token not in allowed_categories and token not in {"top_down", "fixed_palette"}:
            errors.append("unknown_furniture_category")
            break
    visible = architecture_summary.get("visible_architecture_elements", {})
    claims = set(map(str, output.get("architecture_claims") or []))
    # Claims are advisory metadata from the LLM; the deterministic
    # architecture_summary controls the final Architecture_Control text.
    intent_only = str(output.get("user_intent_prompt") or output.get("compiled_text_prompt") or "")
    if re.search(r"\bwall(s)?\b", intent_only, re.IGNORECASE) and not visible.get("wall_class"):
        errors.append("wall_claim_not_visible")
    if re.search(r"clearance\s+regions?\s+(?:are\s+)?visible|visible\s+clearance|non-placeable|non placeable", intent_only, re.IGNORECASE):
        errors.append("unsupported_architecture_visibility_claim")
    return errors, prompt, active, active_entries


def compile_prompt_package_llm(goal_lostate: dict[str, Any], architecture_summary: dict[str, Any] | None = None, registry: Any | None = None, llm_client: PromptLLMClient | None = None, fallback: bool = True) -> dict[str, Any]:
    architecture_summary = architecture_summary or build_architecture_summary(None)
    if llm_client is None:
        if not fallback:
            raise ValueError("llm_client is required when fallback is disabled")
        package = compile_prompt_package_rule(goal_lostate, architecture_summary, registry)
        package["prompt_compiler_mode"] = "llm_with_rule_fallback"
        package["llm_prompt_compiler_report"] = {"used_llm": False, "fallback_used": True, "validation_status": "fallback_no_llm_client"}
        return package
    payload = _safe_goal_payload(goal_lostate, architecture_summary, registry)
    try:
        output = _parse_llm_output(llm_client.generate_json(SYSTEM_PROMPT, payload))
        errors, prompt, active_categories, active_palette_entries = validate_llm_prompt_output(output, goal_lostate, architecture_summary, registry)
    except Exception as exc:
        output = {}
        prompt = ""
        active_categories = _active_categories(goal_lostate)
        active_palette_entries = _palette_entries(active_categories, registry)
        errors = [f"llm_parse_error:{type(exc).__name__}"]
    if errors:
        if not fallback:
            raise ValueError(f"LLM prompt compiler validation failed: {errors}")
        package = compile_prompt_package_rule(goal_lostate, architecture_summary, registry)
        package["prompt_compiler_mode"] = "llm_with_rule_fallback"
        package["llm_prompt_compiler_report"] = {"used_llm": True, "fallback_used": True, "validation_status": "fallback_validation_failed", "validation_errors": errors}
        return package
    return {
        "schema_version": "prompt-package-v3",
        "task_id": goal_lostate.get("metadata", {}).get("task_id", "unknown_task"),
        "prompt_compiler_mode": "llm_functional",
        "compiled_text_prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "active_palette_categories": active_categories,
        "active_palette_entries": active_palette_entries,
        "prompt_constraint_refs": output.get("used_constraint_ids") or [],
        "verifier_only_constraint_refs": output.get("omitted_constraint_ids") or [],
        "constraint_routes": {cid: "prompt" for cid in output.get("used_constraint_ids") or []},
        "llm_prompt_compiler_report": {"used_llm": True, "fallback_used": False, "validation_status": "pass", "architecture_claims": output.get("architecture_claims") or [], "used_slot_ids": output.get("used_slot_ids") or [], "notes": output.get("notes") or [], "llm_user_intent_prompt": output.get("user_intent_prompt") or output.get("compiled_text_prompt")},
    }
