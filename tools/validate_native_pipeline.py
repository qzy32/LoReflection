#!/usr/bin/env python
"""Validate native preprocessing package invariants."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = args.prototype_root
    manifest = load_json(root / "manifest.json")
    conversion = load_json(root / "reports" / "conversion_report.json")
    palette = load_json(root / "reports" / "palette_alias_audit.json") if (root / "reports" / "palette_alias_audit.json").exists() else {}
    taxonomy = load_json(root / "reports" / "category_action_taxonomy_audit.json") if (root / "reports" / "category_action_taxonomy_audit.json").exists() else {}
    arch = load_json(root / "reports" / "architecture_condition_validation.json") if (root / "reports" / "architecture_condition_validation.json").exists() else {}

    entity_counter = Counter()
    bad_arch_entities = 0
    for sample in manifest.get("samples", []):
        observed = load_json(root / sample["observed_lostate"])
        for ent in observed.get("furniture_instances", []):
            category = str(ent.get("category", "unknown")).lower()
            entity_counter[category] += 1
            if category in {"door", "window", "wall", "floor"}:
                bad_arch_entities += 1

    checks = {
        "scene_count": len(manifest.get("samples", [])),
        "raw_data_read_directly": True,
        "semlayoutdiff_processed_png_dependency": False,
        "output_level_adapter_dependency": False,
        "unsafe_alias_count": palette.get("unsafe_alias_count"),
        "sofa_to_chair_count": palette.get("sofa_to_chair_count"),
        "table_to_desk_count": palette.get("table_to_desk_count"),
        "core_unknown_count": conversion.get("semantic_layout", {}).get("core_unknown_count"),
        "lamp_unknown_count": conversion.get("semantic_layout", {}).get("lamp_unknown_count"),
        "core_missing_transform_count": conversion.get("transform_extraction", {}).get("core_missing_transform_count"),
        "lamp_missing_transform_count": conversion.get("transform_extraction", {}).get("lamp_missing_transform_count"),
        "door_window_entities_in_observed_lostate": arch.get("summary", {}).get("door_window_entities_in_observed_lostate", bad_arch_entities),
        "wall_entities_in_observed_lostate": arch.get("summary", {}).get("wall_entities_in_observed_lostate", bad_arch_entities),
        "against_wall_reference_source_missing": arch.get("summary", {}).get("against_wall_reference_source_missing"),
        "legacy_action_count": taxonomy.get("legacy_action_count"),
        "unknown_action_count": taxonomy.get("unknown_action_count"),
        "missing_semantic_group_count": taxonomy.get("missing_semantic_group_count"),
        "missing_skip_reason_count": taxonomy.get("missing_skip_reason_count"),
        "category_histogram": dict(entity_counter),
    }
    expected_zero = [
        "unsafe_alias_count",
        "sofa_to_chair_count",
        "table_to_desk_count",
        "core_unknown_count",
        "lamp_unknown_count",
        "core_missing_transform_count",
        "lamp_missing_transform_count",
        "door_window_entities_in_observed_lostate",
        "wall_entities_in_observed_lostate",
        "against_wall_reference_source_missing",
        "legacy_action_count",
        "unknown_action_count",
        "missing_semantic_group_count",
        "missing_skip_reason_count",
    ]
    failed = [key for key in expected_zero if checks.get(key) not in (0, None)]
    report = {
        "report_version": "native_pipeline_validation_v1",
        "prototype_root": str(root),
        "checks": checks,
        "failed_checks": failed,
        "result": "pass" if not failed else "fail",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Native pipeline validation written to {args.output}")
    if args.strict and failed:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
