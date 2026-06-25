#!/usr/bin/env python
"""Compare the legacy prototype package with the native preprocessing package."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


IGNORE_ENTITY_FIELDS = {"mapping_action", "semantic_group", "warnings", "uncertainty"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def rel_path(root: Path, maybe_rel: str) -> Path:
    p = Path(maybe_rel)
    return p if p.is_absolute() else root / p


def load_manifest(root: Path) -> dict[str, Any]:
    return load_json(root / "manifest.json")


def sample_by_scene(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {sample["scene_id"]: sample for sample in manifest.get("samples", [])}


def normalize_entity(entity: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in entity.items() if k not in IGNORE_ENTITY_FIELDS}


def load_entities(root: Path, sample: dict[str, Any]) -> list[dict[str, Any]]:
    observed_path = rel_path(root, sample["observed_lostate"])
    observed = load_json(observed_path)
    return observed.get("furniture_instances") or observed.get("entities") or []


def category_histogram(entities: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(e.get("category", "unknown")) for e in entities))


def arch_payload(root: Path, sample: dict[str, Any]) -> dict[str, Any]:
    arch = load_json(rel_path(root, sample["architecture_json"]))
    for key in ["source", "metadata"]:
        if isinstance(arch.get(key), dict):
            arch[key].pop("output_root", None)
    return arch


def compare(old_root: Path, new_root: Path) -> dict[str, Any]:
    old_manifest = load_manifest(old_root)
    new_manifest = load_manifest(new_root)
    old_samples = sample_by_scene(old_manifest)
    new_samples = sample_by_scene(new_manifest)
    scene_ids = sorted(set(old_samples) | set(new_samples))
    differences: list[dict[str, Any]] = []
    totals = {
        "old_entity_count": 0,
        "new_entity_count": 0,
        "old_category_histogram": Counter(),
        "new_category_histogram": Counter(),
    }
    image_results = {"semantic_same": 0, "architecture_condition_same": 0, "semantic_different": 0, "architecture_condition_different": 0}
    entity_geometry_same = 0
    architecture_geometry_same = 0

    for scene_id in scene_ids:
        if scene_id not in old_samples or scene_id not in new_samples:
            differences.append({"scene_id": scene_id, "kind": "scene_set", "classification": "unexpected_regression"})
            continue
        old_sample = old_samples[scene_id]
        new_sample = new_samples[scene_id]

        old_entities = load_entities(old_root, old_sample)
        new_entities = load_entities(new_root, new_sample)
        totals["old_entity_count"] += len(old_entities)
        totals["new_entity_count"] += len(new_entities)
        totals["old_category_histogram"].update(category_histogram(old_entities))
        totals["new_category_histogram"].update(category_histogram(new_entities))

        if [normalize_entity(e) for e in old_entities] == [normalize_entity(e) for e in new_entities]:
            entity_geometry_same += 1
        else:
            differences.append({
                "scene_id": scene_id,
                "kind": "observed_lostate",
                "classification": "unexpected_regression",
                "old_count": len(old_entities),
                "new_count": len(new_entities),
            })

        if arch_payload(old_root, old_sample) == arch_payload(new_root, new_sample):
            architecture_geometry_same += 1
        else:
            differences.append({"scene_id": scene_id, "kind": "architecture_json", "classification": "unexpected_regression"})

        for field, same_key, diff_key in [
            ("semantic_layout", "semantic_same", "semantic_different"),
            ("architecture_condition", "architecture_condition_same", "architecture_condition_different"),
        ]:
            if sha256(rel_path(old_root, old_sample[field])) == sha256(rel_path(new_root, new_sample[field])):
                image_results[same_key] += 1
            else:
                image_results[diff_key] += 1
                differences.append({
                    "scene_id": scene_id,
                    "kind": field,
                    "classification": "unknown difference",
                    "note": "Image hash differs; inspect only if native source-aligned renderer intentionally changed.",
                })

    old_report = load_json(old_root / "reports" / "conversion_report.json")
    new_report = load_json(new_root / "reports" / "conversion_report.json")
    old_palette = load_json(old_root / "reports" / "palette_alias_audit.json") if (old_root / "reports" / "palette_alias_audit.json").exists() else {}
    new_palette = load_json(new_root / "reports" / "palette_alias_audit.json") if (new_root / "reports" / "palette_alias_audit.json").exists() else {}
    new_taxonomy = load_json(new_root / "reports" / "category_action_taxonomy_audit.json") if (new_root / "reports" / "category_action_taxonomy_audit.json").exists() else {}
    arch_validation = load_json(new_root / "reports" / "architecture_condition_validation.json") if (new_root / "reports" / "architecture_condition_validation.json").exists() else {}

    regression_checks = {
        "unsafe_alias_count": new_palette.get("unsafe_alias_count"),
        "sofa_to_chair_count": new_palette.get("sofa_to_chair_count"),
        "table_to_desk_count": new_palette.get("table_to_desk_count"),
        "core_unknown_count": new_report.get("semantic_layout", {}).get("core_unknown_count"),
        "lamp_unknown_count": new_report.get("semantic_layout", {}).get("lamp_unknown_count"),
        "core_missing_transform_count": new_report.get("transform_extraction", {}).get("core_missing_transform_count"),
        "lamp_missing_transform_count": new_report.get("transform_extraction", {}).get("lamp_missing_transform_count"),
        "door_window_entities_in_observed_lostate": arch_validation.get("summary", {}).get("door_window_entities_in_observed_lostate"),
        "wall_entities_in_observed_lostate": arch_validation.get("summary", {}).get("wall_entities_in_observed_lostate"),
        "against_wall_reference_source_missing": arch_validation.get("summary", {}).get("against_wall_reference_source_missing"),
        "legacy_action_count": new_taxonomy.get("legacy_action_count"),
        "unknown_action_count": new_taxonomy.get("unknown_action_count"),
        "missing_semantic_group_count": new_taxonomy.get("missing_semantic_group_count"),
        "missing_skip_reason_count": new_taxonomy.get("missing_skip_reason_count"),
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
    failed_checks = [k for k in expected_zero if regression_checks.get(k) not in (0, None)]
    unexpected = [d for d in differences if d.get("classification") == "unexpected_regression"]

    return {
        "report_version": "native_vs_adapter_comparison_v1",
        "old_root": str(old_root),
        "new_root": str(new_root),
        "scene_ids": scene_ids,
        "scene_count": len(scene_ids),
        "entity_counts": {"old": totals["old_entity_count"], "new": totals["new_entity_count"]},
        "category_histograms": {
            "old": dict(totals["old_category_histogram"]),
            "new": dict(totals["new_category_histogram"]),
        },
        "semantic_images": image_results,
        "entity_geometry_identical_scene_count": entity_geometry_same,
        "architecture_geometry_identical_scene_count": architecture_geometry_same,
        "old_conversion_summary": old_report.get("summary", {}),
        "new_conversion_summary": new_report.get("summary", {}),
        "differences": differences,
        "regression_checks": regression_checks,
        "failed_regression_checks": failed_checks,
        "result": "pass" if not failed_checks and not unexpected else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-root", required=True, type=Path)
    parser.add_argument("--new-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = compare(args.old_root, args.new_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Native vs adapter comparison written to {args.output}")
    if args.strict and report["result"] != "pass":
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
