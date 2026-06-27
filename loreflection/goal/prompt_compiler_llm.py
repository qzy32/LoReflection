"""Constrained LLM Prompt Compiler for Goal LoState verbalization."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from .prompt_compiler_rule import LEAKAGE_REGEX, NEGATIVE_PROMPT, _active_categories, _palette_entries, compile_prompt_package_rule

SYSTEM_PROMPT = """You are a prompt compiler for fixed-palette semantic top-down indoor layout generation.
Your job is to verbalize a symbolic Goal LoState into a concise prompt for Qwen-Image Architecture In-Context Control.
The final prompt must contain Context_Control, Architecture_Control, and Palette_Control sections.
Palette_Control must list every active semantic category provided in the input.
Do not invent furniture categories.
Do not invent doors, windows, walls, clearance regions, or non-placeable regions.
Only mention architecture elements listed as visible in architecture_summary.
Do not include coordinates, dimensions, pixels, bounding boxes, metric units, JSON paths, or object ids.
Do not output layout JSON.
Do not output furniture positions.
Output only valid JSON matching the schema."""

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
    palette = getattr(registry, "palette", None) if registry is not None else None
    if not isinstance(palette, dict):
        palette = getattr(registry, "colors", None) if registry is not None else None
    if isinstance(palette, dict):
        cats.update(str(k) for k in palette if k not in {"void", "floor", "door", "window"})
    return cats


def _slot_ids(goal_lostate: dict[str, Any]) -> set[str]:
    return {str(slot.get("slot_id")) for slot in goal_lostate.get("furniture_slots", []) if isinstance(slot, dict) and slot.get("slot_id")}


def _constraint_ids(goal_lostate: dict[str, Any]) -> set[str]:
    return {str(c.get("constraint_id")) for c in goal_lostate.get("goal_constraints", []) if isinstance(c, dict) and c.get("constraint_id")}


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
            "compiled_text_prompt": "string with Context_Control, Architecture_Control, Palette_Control",
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
    return json.loads(text)


def validate_llm_prompt_output(output: dict[str, Any], goal_lostate: dict[str, Any], architecture_summary: dict[str, Any], registry: Any | None = None) -> list[str]:
    errors: list[str] = []
    prompt = output.get("compiled_text_prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        errors.append("compiled_text_prompt_missing")
        prompt = ""
    if len(WORD_SPLIT.findall(prompt.strip())) > 140:
        errors.append("compiled_text_prompt_too_long")
    if any(regex.search(prompt) for regex in LEAKAGE_REGEX):
        errors.append("geometry_leakage")
    if "{" in prompt or "layout_json" in prompt or "scene_json" in prompt:
        errors.append("layout_json_leakage")
    for section in ["Context_Control.", "Architecture_Control.", "Palette_Control."]:
        if section not in prompt:
            errors.append(f"missing_{section.split('.')[0].lower()}")

    active = _active_categories(goal_lostate)
    if not all(category in prompt for category in active):
        errors.append("active_category_missing_from_prompt")

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
    if "visible_door" in claims and not visible.get("door"):
        errors.append("invalid_door_claim")
    if "visible_window" in claims and not visible.get("window"):
        errors.append("invalid_window_claim")
    if any(claim in claims for claim in ["visible_wall", "clearance_region", "non_placeable_region"]):
        errors.append("invalid_architecture_claim")
    if re.search(r"\bwall(s)?\b", prompt, re.IGNORECASE) and not visible.get("wall_class"):
        errors.append("wall_claim_not_visible")
    if re.search(r"clearance|non-placeable|non placeable", prompt, re.IGNORECASE):
        errors.append("unsupported_architecture_visibility_claim")
    return errors


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
        errors = validate_llm_prompt_output(output, goal_lostate, architecture_summary, registry)
    except Exception as exc:
        output = {}
        errors = [f"llm_parse_error:{type(exc).__name__}"]
    if errors:
        if not fallback:
            raise ValueError(f"LLM prompt compiler validation failed: {errors}")
        package = compile_prompt_package_rule(goal_lostate, architecture_summary, registry)
        package["prompt_compiler_mode"] = "llm_with_rule_fallback"
        package["llm_prompt_compiler_report"] = {"used_llm": True, "fallback_used": True, "validation_status": "fallback_validation_failed", "validation_errors": errors}
        return package
    active_categories = _active_categories(goal_lostate)
    active_palette_entries = _palette_entries(active_categories, registry)
    prompt = output["compiled_text_prompt"].strip()
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
        "llm_prompt_compiler_report": {"used_llm": True, "fallback_used": False, "validation_status": "pass", "architecture_claims": output.get("architecture_claims") or [], "used_slot_ids": output.get("used_slot_ids") or [], "notes": output.get("notes") or []},
    }
