#!/usr/bin/env python3
"""Validate the current LoReflection RepairPlan contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
REPAIRPLAN_SCHEMA = ROOT / "artifacts/current_interface/repairplan.schema.json"
MASK_SPEC_SCHEMA = ROOT / "artifacts/current_interface/mask_spec.schema.json"

CANONICAL_ACTIONS = {"ADD", "REMOVE", "TRANSLATE", "ROTATE", "SCALE", "REPLACE"}
SEMANTIC_REPAIR4 = {"ADD", "REMOVE", "TRANSLATE", "REPLACE"}
PARAMETRIC_UPDATE_ACTIONS = {"ROTATE", "SCALE"}
FLOOR_SEMANTIC_ID = 1
OLD_ALIASES = {
    "IN" + "SERT",
    "DE" + "LETE",
    "MO" + "VE",
    "RE" + "SIZE",
    "UPDATE" + "_YAW",
    "UPDATE" + "_SIZE",
}
FORBIDDEN_TEXT = {
    "semantic" + "_inpaint",
    "hy" + "brid",
    "apm" + "_attribute_update",
    "control_mask.png",
    "binary_mask",
    "blockwise_controlnet_image",
    "blockwise_controlnet_inpaint_mask",
    "metadata.csv",
    "raw_repaired_image",
    "repaired_image",
}


class ValidationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_validate(instance: dict[str, Any], schema_path: Path) -> None:
    validator = Draft202012Validator(_load_schema(schema_path))
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise ValidationError(f"schema validation failed at {location}: {first.message}")


def _components(plan: dict[str, Any]) -> list[dict[str, Any]]:
    spec = plan.get("mask_spec") or {}
    return list(spec.get("components") or [])


def _components_by_role(plan: dict[str, Any], role: str) -> list[dict[str, Any]]:
    return [component for component in _components(plan) if component.get("component_role") == role]


def _roles(plan: dict[str, Any]) -> set[str]:
    return {component.get("component_role") for component in _components(plan)}


def _target_delta(plan: dict[str, Any]) -> dict[str, Any]:
    return plan.get("target_state_delta") or {}


def _allowed_labels(component: dict[str, Any]) -> set[int]:
    return set(component.get("allowed_labels") or [])


def _check_bbox(component: dict[str, Any], image_size: list[int]) -> None:
    if component.get("geometry_type") != "bbox":
        return
    bbox = component.get("geometry", {}).get("bbox_px")
    _require(isinstance(bbox, list) and len(bbox) == 4, "bbox component requires bbox_px")
    x1, y1, x2, y2 = bbox
    _require(x2 > x1 and y2 > y1, "bbox_px must satisfy x2 > x1 and y2 > y1")
    width, height = image_size
    _require(0 <= x1 < width and 0 < x2 <= width, "bbox_px x coordinates outside image bounds")
    _require(0 <= y1 < height and 0 < y2 <= height, "bbox_px y coordinates outside image bounds")


def _validate_mask_spec(plan: dict[str, Any]) -> None:
    spec = plan.get("mask_spec")
    if spec is None:
        return
    _schema_validate(spec, MASK_SPEC_SCHEMA)
    image_size = spec.get("image_size_px") or [512, 512]
    for component in spec.get("components", []):
        _check_bbox(component, image_size)
        role = component.get("component_role")
        op = component.get("operation_hint")
        if role == "target_region":
            _require(op in {"paint_target", "preserve", "context_only"}, "target_region should paint target or preserve/context")
        if role == "old_region":
            _require(op == "clear_to_floor", "old_region must clear_to_floor")
        if role == "new_region":
            _require(op == "paint_target", "new_region must paint_target")
        if role == "source_region" and plan.get("action_type") == "REMOVE":
            _require(op == "clear_to_floor", "REMOVE source_region must clear_to_floor")
        if role == "protected_region":
            _require(op == "preserve", "protected_region must preserve")


def validate_plan(plan: dict[str, Any]) -> None:
    _schema_validate(plan, REPAIRPLAN_SCHEMA)
    _validate_mask_spec(plan)

    action = plan.get("action_type")
    mode = plan.get("execution_mode")
    _require(action in CANONICAL_ACTIONS, f"invalid action_type: {action}")
    _require(action not in OLD_ALIASES, f"old alias action is not allowed: {action}")
    _require(mode in {"semantic_repair", "parametric_update"}, f"invalid execution_mode: {mode}")

    text = json.dumps(plan, ensure_ascii=False)
    for bad in FORBIDDEN_TEXT:
        _require(bad not in text, f"deprecated or forbidden executor artifact present: {bad}")

    delta = _target_delta(plan)
    roles = _roles(plan)

    if action in SEMANTIC_REPAIR4:
        _require(mode == "semantic_repair", f"{action} must use semantic_repair")
        _require(plan.get("mask_spec") is not None, f"{action} requires mask_spec")
        _require(bool(plan.get("correction_prompt")), f"{action} requires correction_prompt")
    if action in PARAMETRIC_UPDATE_ACTIONS:
        _require(mode == "parametric_update", f"{action} must use parametric_update")
        _require(plan.get("mask_spec") is None, f"{action} must not include mask_spec")
        _require(plan.get("correction_prompt") is None, f"{action} must not include correction_prompt")
        _require(plan.get("parametric_delta") not in (None, {}), f"{action} requires parametric_delta")
        _require(bool(plan.get("target_instance_ref")), f"{action} requires target_instance_ref")

    if action == "ADD":
        _require(plan.get("parametric_delta") is None, "ADD must not include parametric_delta")
        _require(delta.get("target_count_delta") == 1, "ADD requires target_count_delta = +1")
        _require("target_region" in roles, "ADD requires target_region")
        target_id = delta.get("target_semantic_id")
        _require(target_id is not None, "ADD requires target_semantic_id")
        for component in _components_by_role(plan, "target_region"):
            _require(component.get("operation_hint") == "paint_target", "ADD target_region must paint_target")
            _require(target_id in _allowed_labels(component), "ADD target_region allowed_labels must contain target_semantic_id")
    elif action == "REMOVE":
        _require(plan.get("parametric_delta") is None, "REMOVE must not include parametric_delta")
        _require(delta.get("target_count_delta") == -1, "REMOVE requires target_count_delta = -1")
        _require(bool(plan.get("source_instance_ref")), "REMOVE requires source_instance_ref")
        _require("source_region" in roles, "REMOVE requires source_region")
        for component in _components_by_role(plan, "source_region"):
            _require(component.get("operation_hint") == "clear_to_floor", "REMOVE source_region must clear_to_floor")
            _require(FLOOR_SEMANTIC_ID in _allowed_labels(component), "REMOVE source_region allowed_labels must contain floor semantic id")
    elif action == "TRANSLATE":
        _require(delta.get("target_count_delta") == 0, "TRANSLATE requires target_count_delta = 0")
        _require({"old_region", "new_region"}.issubset(roles), "TRANSLATE requires old_region + new_region")
        _require(plan["mask_spec"].get("allow_disconnected") is True, "TRANSLATE requires allow_disconnected = true")
        parametric_delta = plan.get("parametric_delta")
        if parametric_delta is not None:
            _require(parametric_delta.get("bookkeeping_only") is True, "TRANSLATE parametric_delta must be bookkeeping_only")
        for component in _components_by_role(plan, "old_region"):
            _require(component.get("operation_hint") == "clear_to_floor", "TRANSLATE old_region must clear_to_floor")
        for component in _components_by_role(plan, "new_region"):
            _require(component.get("operation_hint") == "paint_target", "TRANSLATE new_region must paint_target")
    elif action == "REPLACE":
        _require(plan.get("parametric_delta") is None, "REPLACE must not include parametric_delta")
        _require(delta.get("target_count_delta") == 0, "REPLACE requires target_count_delta = 0")
        _require(bool(plan.get("source_instance_ref")), "REPLACE requires source_instance_ref")
        for key in ("source_category", "source_semantic_id", "target_category", "target_semantic_id"):
            _require(delta.get(key) is not None, f"REPLACE requires {key}")
        _require({"source_region", "target_region"}.issubset(roles), "REPLACE requires source_region + target_region")
        target_id = delta.get("target_semantic_id")
        for component in _components_by_role(plan, "source_region"):
            _require(component.get("operation_hint") in {"replace_source", "clear_to_floor"}, "REPLACE source_region must replace_source or clear_to_floor")
        for component in _components_by_role(plan, "target_region"):
            _require(component.get("operation_hint") == "paint_target", "REPLACE target_region must paint_target")
            _require(target_id in _allowed_labels(component), "REPLACE target_region allowed_labels must contain target_semantic_id")
    elif action == "ROTATE":
        pdelta = plan.get("parametric_delta") or {}
        _require("rotation_deg" in pdelta or "new_yaw_rad" in pdelta, "ROTATE requires rotation_deg or new_yaw_rad")
    elif action == "SCALE":
        pdelta = plan.get("parametric_delta") or {}
        _require("scale_xy" in pdelta or "new_size" in pdelta, "SCALE requires scale_xy or new_size")


def extract_plans(path: Path, sft_jsonl: bool) -> list[dict[str, Any]]:
    if sft_jsonl:
        plans = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            answer = row["conversations"][-1]["value"]
            plans.append(json.loads(answer))
        return plans
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--sft-jsonl", action="store_true")
    args = parser.parse_args()
    for plan in extract_plans(args.path, args.sft_jsonl):
        validate_plan(plan)
    print(f"validated {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
