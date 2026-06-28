"""LLM-only Functional Prompt Compiler for Qwen architecture control."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from .prompt_package_validator import (
    ERROR_CLIENT_MISSING,
    ERROR_JSON_INVALID,
    NEGATIVE_PROMPT,
    PromptCompilerError,
    active_categories,
    active_palette_entries,
    allowed_constraint_ids,
    allowed_slot_ids,
    raise_if_invalid,
    registry_palette,
    validate_prompt_package,
)

SYSTEM_PROMPT = """You are an LLM Functional Prompt Compiler for fixed-palette top-down indoor semantic layout generation.

Your task is to verbalize a symbolic Goal LoState into one concise English prompt for Qwen-Image Architecture In-Context Control.

You must not generate coordinates, dimensions, bounding boxes, object positions, layout JSON, or StatePatch JSON.

You must not invent furniture categories. Use only allowed semantic categories.

You must not invent architecture elements. Only mention room floor boundary, doors, windows, walls, clearance regions, or non-placeable regions if architecture_summary says they are visible.

You must not include raw field names such as center_m, size_m, bbox, footprint, pixel, px, cm, meter, coordinate, source_json_path, or uid.

The compiled_text_prompt must contain exactly these three labeled sections in order:
Context_Control. ...
Architecture_Control. ...
Palette_Control. ...

Architecture_Control may mention only visible elements from architecture_summary. Do not mention visible windows when window is false. Do not use the words pixel, px, cm, meter, coordinate, bbox, or footprint.

Palette_Control must mention the frozen semantic palette. The program will append active RGB palette entries after validation.

Output only valid JSON matching the requested schema."""


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


def _parse_llm_output(raw: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    text = str(raw).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise PromptCompilerError(ERROR_JSON_INVALID, str(exc)) from exc
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc2:
            raise PromptCompilerError(ERROR_JSON_INVALID, str(exc2)) from exc2


def _safe_goal_payload(goal_lostate: dict[str, Any], architecture_summary: dict[str, Any], registry: Any | None) -> dict[str, Any]:
    slots = []
    for slot in goal_lostate.get("furniture_slots", []) or []:
        if isinstance(slot, dict):
            slots.append({k: slot.get(k) for k in ("slot_id", "category", "count", "required", "role") if k in slot})
    constraints = []
    for constraint in goal_lostate.get("goal_constraints", []) or []:
        if isinstance(constraint, dict):
            constraints.append({k: constraint.get(k) for k in ("constraint_id", "constraint_kind", "necessity", "prompt_hint", "intent_tag") if k in constraint})
    return {
        "room_type": goal_lostate.get("room_type"),
        "furniture_slots": slots,
        "goal_constraints": constraints,
        "prompt_compilation_policy": goal_lostate.get("prompt_compilation_policy") or {},
        "allowed_furniture_categories": sorted(k for k in registry_palette(registry) if k not in {"void", "floor", "door", "window"}),
        "active_palette_categories": active_categories(goal_lostate),
        "active_palette_entries": active_palette_entries(goal_lostate, registry),
        "architecture_summary": architecture_summary,
        "output_schema": {
            "compiled_text_prompt": "one concise English Qwen prompt with Context_Control, Architecture_Control, and Palette_Control sections",
            "required_prompt_sections": ["Context_Control", "Architecture_Control", "Palette_Control"],
            "used_slot_ids": sorted(allowed_slot_ids(goal_lostate)),
            "used_constraint_ids": sorted(allowed_constraint_ids(goal_lostate)),
            "omitted_constraint_ids": sorted(allowed_constraint_ids(goal_lostate)),
            "allowed_architecture_claims": [
                claim for claim, enabled in {
                    "room_floor_boundary": architecture_summary.get("visible_architecture_elements", {}).get("room_floor_boundary", False),
                    "visible_door": architecture_summary.get("visible_architecture_elements", {}).get("door", False),
                    "visible_window": architecture_summary.get("visible_architecture_elements", {}).get("window", False),
                    "wall_class": architecture_summary.get("visible_architecture_elements", {}).get("wall_class", False),
                    "clearance_region": architecture_summary.get("visible_architecture_elements", {}).get("clearance_region", False),
                    "non_placeable_region": architecture_summary.get("visible_architecture_elements", {}).get("non_placeable_region", False),
                }.items() if enabled
            ],
            "notes": [],
        },
    }


def _palette_control_suffix(goal_lostate: dict[str, Any], registry: Any | None) -> str:
    entries = active_palette_entries(goal_lostate, registry)
    mapping = ", ".join(f"{cat}=({rgb[0]},{rgb[1]},{rgb[2]})" for cat, rgb in sorted(entries.items())) or "none"
    return " Use only the frozen semantic palette. Active semantic category RGB palette entries: " + mapping + "."


def compile_prompt_package(
    goal_lostate: dict[str, Any],
    architecture_summary: dict[str, Any] | None = None,
    registry: Any | None = None,
    llm_client: PromptLLMClient | None = None,
) -> dict[str, Any]:
    if llm_client is None:
        raise PromptCompilerError(ERROR_CLIENT_MISSING)
    architecture_summary = architecture_summary or build_architecture_summary(None)
    payload = _safe_goal_payload(goal_lostate, architecture_summary, registry)
    output = _parse_llm_output(llm_client.generate_json(SYSTEM_PROMPT, payload))
    prompt = str(output.get("compiled_text_prompt") or "").strip()
    suffix = _palette_control_suffix(goal_lostate, registry)
    if suffix.strip() not in prompt:
        prompt = (prompt.rstrip(" .") + "." + suffix).strip()
    package = {
        "schema_version": "prompt-package-v3",
        "prompt_compiler": "llm_functional",
        "compiled_text_prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "used_slot_ids": output.get("used_slot_ids") or [],
        "used_constraint_ids": output.get("used_constraint_ids") or [],
        "omitted_constraint_ids": output.get("omitted_constraint_ids") or [],
        "architecture_claims": output.get("architecture_claims") or [],
        "constraint_routes": {str(cid): "prompt" for cid in output.get("used_constraint_ids") or []},
        "validation_report": {},
        "llm_request": payload,
        "llm_raw_response": output,
    }
    report = validate_prompt_package(package, goal_lostate, architecture_summary, registry)
    package["validation_report"] = report
    raise_if_invalid(report)
    return package
