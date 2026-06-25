#!/usr/bin/env python
"""Audit canonical category action taxonomy for a LoReflection prototype."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


CANONICAL_ACTIONS = {"keep_furniture", "keep_architecture_anchor", "keep_architecture_region", "skip"}
LEGACY_ACTIONS = {"keep_core", "keep_lamp", "architecture_anchor", "architecture_region", "skip_accessory", "skip_unknown"}
SEMANTIC_GROUPS = {"core_furniture", "lighting", "architecture", "accessory", "unknown"}
ARCHITECTURE_CATEGORIES = {"door", "window", "wall", "floor", "opening", "architecture"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def audit_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    action_counts = Counter()
    group_counts = Counter()
    skip_reason_counts = Counter()
    legacy_action_count = 0
    unknown_action_count = 0
    missing_semantic_group_count = 0
    missing_skip_reason_count = 0
    keep_furniture_missing_category_count = 0
    rows = list(mapping.get("rules", [])) + [mapping.get("default", {})]
    bad_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        action = row.get("action")
        group = row.get("semantic_group")
        action_counts[str(action)] += 1
        group_counts[str(group)] += 1
        if action in LEGACY_ACTIONS:
            legacy_action_count += 1
            bad_rows.append({"index": idx, "reason": "legacy_action", "row": row})
        if action not in CANONICAL_ACTIONS:
            unknown_action_count += 1
            bad_rows.append({"index": idx, "reason": "unknown_action", "row": row})
        if group not in SEMANTIC_GROUPS:
            missing_semantic_group_count += 1
            bad_rows.append({"index": idx, "reason": "missing_or_invalid_semantic_group", "row": row})
        if action == "keep_furniture" and not row.get("loreflection_category"):
            keep_furniture_missing_category_count += 1
            bad_rows.append({"index": idx, "reason": "keep_furniture_missing_category", "row": row})
        if action == "skip":
            reason = row.get("skip_reason")
            if group in {"accessory", "unknown"} and not reason:
                missing_skip_reason_count += 1
                bad_rows.append({"index": idx, "reason": "missing_skip_reason", "row": row})
            if reason:
                skip_reason_counts[str(reason)] += 1
    return {
        "mapping_entry_count": len(rows),
        "canonical_action_counts": {k: v for k, v in action_counts.items() if k in CANONICAL_ACTIONS},
        "semantic_group_counts": dict(group_counts),
        "skip_reason_counts": dict(skip_reason_counts),
        "legacy_action_count": legacy_action_count,
        "unknown_action_count": unknown_action_count,
        "missing_semantic_group_count": missing_semantic_group_count,
        "missing_skip_reason_count": missing_skip_reason_count,
        "keep_furniture_missing_category_count": keep_furniture_missing_category_count,
        "bad_mapping_rows": bad_rows,
    }


def audit_prototype(prototype_root: Path) -> dict[str, Any]:
    observed_entity_non_furniture_action_count = 0
    architecture_entity_in_observed_lostate_count = 0
    legacy_entity_action_count = 0
    missing_entity_group_count = 0
    action_counts = Counter()
    group_counts = Counter()
    bad_entities: list[dict[str, Any]] = []
    for path in sorted((prototype_root / "observed_lostate_v1").glob("*.json")):
        observed = load_json(path)
        scene_id = observed.get("metadata", {}).get("task_id", path.stem)
        for entity in observed.get("furniture_instances", []):
            action = entity.get("mapping_action")
            group = entity.get("semantic_group")
            category = str(entity.get("category") or entity.get("loreflection_category") or "").lower()
            action_counts[str(action)] += 1
            group_counts[str(group)] += 1
            if action in LEGACY_ACTIONS:
                legacy_entity_action_count += 1
            if action != "keep_furniture":
                observed_entity_non_furniture_action_count += 1
                bad_entities.append({"scene_id": scene_id, "instance_id": entity.get("instance_id"), "reason": "non_furniture_action", "action": action})
            if group not in {"core_furniture", "lighting"}:
                missing_entity_group_count += 1
                bad_entities.append({"scene_id": scene_id, "instance_id": entity.get("instance_id"), "reason": "invalid_entity_group", "semantic_group": group})
            if category in ARCHITECTURE_CATEGORIES:
                architecture_entity_in_observed_lostate_count += 1
                bad_entities.append({"scene_id": scene_id, "instance_id": entity.get("instance_id"), "reason": "architecture_category_in_observed", "category": category})
    return {
        "observed_entity_action_counts": dict(action_counts),
        "observed_entity_semantic_group_counts": dict(group_counts),
        "observed_entity_legacy_action_count": legacy_entity_action_count,
        "observed_entity_missing_or_invalid_group_count": missing_entity_group_count,
        "observed_entity_non_furniture_action_count": observed_entity_non_furniture_action_count,
        "architecture_entity_in_observed_lostate_count": architecture_entity_in_observed_lostate_count,
        "bad_observed_entities": bad_entities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category-mapping", type=Path, required=True)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    mapping_report = audit_mapping(load_json(args.category_mapping))
    prototype_report = audit_prototype(args.prototype_root)
    failures = []
    for key in [
        "legacy_action_count",
        "unknown_action_count",
        "missing_semantic_group_count",
        "missing_skip_reason_count",
        "keep_furniture_missing_category_count",
    ]:
        if mapping_report[key] > 0:
            failures.append(f"{key}={mapping_report[key]}")
    for key in [
        "observed_entity_non_furniture_action_count",
        "architecture_entity_in_observed_lostate_count",
    ]:
        if prototype_report[key] > 0:
            failures.append(f"{key}={prototype_report[key]}")
    if prototype_report["observed_entity_legacy_action_count"] > 0:
        failures.append(f"observed_entity_legacy_action_count={prototype_report['observed_entity_legacy_action_count']}")
    if prototype_report["observed_entity_missing_or_invalid_group_count"] > 0:
        failures.append(f"observed_entity_missing_or_invalid_group_count={prototype_report['observed_entity_missing_or_invalid_group_count']}")

    report = {
        "schema_version": "category-action-taxonomy-audit-v1",
        "category_mapping": args.category_mapping.as_posix(),
        "prototype_root": args.prototype_root.as_posix(),
        **mapping_report,
        **prototype_report,
        "failures": failures,
        "status": "failed" if failures else "passed",
    }
    write_json(args.output, report)
    if failures:
        print(f"Category action taxonomy audit failed: {failures}")
        return 1 if args.strict else 0
    print("Category action taxonomy audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
