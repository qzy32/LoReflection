#!/usr/bin/env python3
"""Validate the current LoReflection StatePatch v1.2 contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
STATEPATCH_SCHEMA = ROOT / "artifacts/current_interface/statepatch.schema.json"

FORBIDDEN_KEYS = {"source_json_path"}
FORBIDDEN_TEXT = {"source_json_path"}
UPDATE_FIELDS = {"center_m", "orientation_deg", "size_m", "category", "asset_id", "new_instance"}


class ValidationError(ValueError):
    pass


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_validate(instance: dict[str, Any]) -> None:
    schema = _load_json(STATEPATCH_SCHEMA)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise ValidationError(f"schema validation failed at {location}: {first.message}")


def _walk(value: Any) -> list[Any]:
    out = [value]
    if isinstance(value, dict):
        for key, child in value.items():
            out.append(key)
            out.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            out.extend(_walk(child))
    return out


def validate_statepatch(patch: dict[str, Any]) -> None:
    _schema_validate(patch)

    for item in _walk(patch):
        if not isinstance(item, str):
            continue
        if item in FORBIDDEN_KEYS:
            raise ValidationError(f"forbidden StatePatch key present: {item}")
        matched = next((term for term in FORBIDDEN_TEXT if term in item), None)
        if matched:
            raise ValidationError(f"forbidden StatePatch text present: {matched}")

    target = patch.get("target") or {}
    if not target.get("target_ref"):
        raise ValidationError("target.target_ref is required")
    if not target.get("expected_category"):
        raise ValidationError("target.expected_category is required")

    action = patch.get("action_type")
    updates = patch.get("state_field_updates")
    if action != "REMOVE" and not updates:
        raise ValidationError(f"{action} requires state_field_updates")
    if updates:
        unknown = set(updates) - UPDATE_FIELDS
        if unknown:
            raise ValidationError(f"unsupported state_field_updates: {sorted(unknown)}")


def _assistant_value(row: dict[str, Any]) -> str:
    if "conversations" in row:
        return row["conversations"][-1]["value"]
    if "messages" in row:
        return row["messages"][-1]["content"]
    if "assistant" in row:
        return row["assistant"]
    if "output" in row:
        return row["output"]
    if "statepatch" in row:
        return json.dumps(row["statepatch"], ensure_ascii=False)
    raise ValidationError("SFT JSONL row does not contain conversations/messages/assistant/output/statepatch")


def extract_patches(path: Path, sft_jsonl: bool) -> list[dict[str, Any]]:
    if sft_jsonl:
        patches = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            try:
                patches.append(json.loads(_assistant_value(row)))
            except json.JSONDecodeError as exc:
                raise ValidationError(f"line {line_no}: assistant value is not JSON: {exc}") from exc
        return patches
    data = _load_json(path)
    return data if isinstance(data, list) else [data]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--sft-jsonl", action="store_true")
    args = parser.parse_args()

    patches = extract_patches(args.path, args.sft_jsonl)
    for patch in patches:
        validate_statepatch(patch)
    print(f"validated {len(patches)} StatePatch object(s) from {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
