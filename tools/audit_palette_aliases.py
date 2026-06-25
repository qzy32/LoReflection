#!/usr/bin/env python
"""Audit palette aliases used by a LoReflection prototype package.

The tool is read-only. It inspects Observed LoState entities and reports which
reference categories were merged into existing LoReflection palette categories.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def severity_for(reference: str, loreflection: str, count: int) -> str:
    reference = reference.lower()
    if reference in {"sofa", "table", "cabinet", "bookshelf", "tv_stand"}:
        return "review" if count < 10 else "risky"
    if reference in {"chair", "bed", "nightstand", "wardrobe", "desk"}:
        return "safe"
    if loreflection in {"pendant_lamp", "ceiling_lamp", "lamp"}:
        return "safe"
    return "review"


def reason_for(reference: str, loreflection: str) -> str:
    if reference == "sofa" and loreflection == "chair":
        return "seating_merge"
    if reference == "table" and loreflection == "desk":
        return "table_merge"
    if reference in {"cabinet", "bookshelf", "tv_stand"} and loreflection == "wardrobe":
        return "storage_merge"
    if reference in {"pendant_lamp", "ceiling_lamp", "lamp"}:
        return "lighting_kept_as_palette_class"
    return "coarse_merge"


def is_sofa_to_chair(raw: str, reference: str, loreflection: str) -> bool:
    text = f"{raw} {reference}".lower()
    return "sofa" in text and loreflection.lower() == "chair"


def is_table_to_desk(raw: str, reference: str, loreflection: str) -> bool:
    text = f"{raw} {reference}".lower()
    table_terms = ["dining table", "coffee table", "corner/side table", "table"]
    return any(term in text for term in table_terms) and loreflection.lower() == "desk"


def unsafe_alias_kind(raw: str, reference: str, loreflection: str) -> str | None:
    if is_sofa_to_chair(raw, reference, loreflection):
        return "sofa_to_chair"
    if is_table_to_desk(raw, reference, loreflection):
        return "table_to_desk"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--category-mapping", type=Path, required=True)
    parser.add_argument("--palette", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.prototype_root / "manifest.json")
    conversion = load_json(args.prototype_root / "reports" / "conversion_report.json")
    mapping = load_json(args.category_mapping)
    palette = load_json(args.palette)
    palette_colors = palette.get("colors", {})

    grouped: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    unsafe_entity_rows: list[dict[str, Any]] = []
    unsafe_counts = Counter()
    for path in sorted((args.prototype_root / "observed_lostate_v1").glob("*.json")):
        observed = load_json(path)
        scene_id = observed.get("metadata", {}).get("task_id") or path.stem.replace(".observed_lostate_v1", "")
        for entity in observed.get("furniture_instances", []):
            raw_any = str(entity.get("raw_category") or entity.get("raw_title") or entity.get("raw_super_category") or "unknown")
            ref_any = str(entity.get("reference_category") or "unknown")
            lo_any = str(entity.get("loreflection_category") or entity.get("category") or "unknown")
            unsafe_kind = unsafe_alias_kind(raw_any, ref_any, lo_any)
            if unsafe_kind:
                unsafe_counts[unsafe_kind] += 1
                unsafe_entity_rows.append(
                    {
                        "scene_id": scene_id,
                        "instance_id": entity.get("instance_id"),
                        "raw_category": raw_any,
                        "reference_category": ref_any,
                        "loreflection_category": lo_any,
                        "unsafe_kind": unsafe_kind,
                    }
                )
            if not entity.get("palette_alias_used"):
                continue
            raw_category = raw_any
            reference_category = ref_any
            loreflection_category = lo_any
            action = str(entity.get("mapping_action") or "unknown")
            alias_reason = reason_for(reference_category, loreflection_category)
            key = (raw_category, reference_category, loreflection_category, action, alias_reason)
            row = grouped.setdefault(
                key,
                {
                    "raw_category": raw_category,
                    "reference_category": reference_category,
                    "loreflection_category": loreflection_category,
                    "mapping_action": action,
                    "count": 0,
                    "scene_ids": set(),
                    "palette_alias_used": True,
                    "alias_reason": alias_reason,
                    "severity": "review",
                    "example_entity_ids": [],
                },
            )
            row["count"] += 1
            row["scene_ids"].add(scene_id)
            if len(row["example_entity_ids"]) < 8:
                row["example_entity_ids"].append(entity.get("instance_id"))

    alias_rows = []
    for row in grouped.values():
        row["scene_ids"] = sorted(row["scene_ids"])
        row["severity"] = severity_for(row["reference_category"], row["loreflection_category"], row["count"])
        alias_rows.append(row)
    alias_rows.sort(key=lambda x: (-x["count"], x["reference_category"], x["raw_category"]))

    summary_by_loreflection = Counter()
    summary_by_reason = Counter()
    for row in alias_rows:
        summary_by_loreflection[row["loreflection_category"]] += row["count"]
        summary_by_reason[row["alias_reason"]] += row["count"]

    recommended_updates = []
    must_review = []
    for row in alias_rows:
        if row["severity"] in {"review", "risky"}:
            must_review.append(
                {
                    "reference_category": row["reference_category"],
                    "current_alias": row["loreflection_category"],
                    "count": row["count"],
                    "reason": row["alias_reason"],
                }
            )
        if row["reference_category"] not in palette_colors and row["reference_category"] in {"sofa", "table", "cabinet", "bookshelf", "tv_stand"}:
            recommended_updates.append(
                {
                    "add_palette_category": row["reference_category"],
                    "current_alias": row["loreflection_category"],
                    "count": row["count"],
                    "priority": "medium" if row["count"] < 10 else "high",
                }
            )

    expected_aliases = [
        "Dining Table -> table",
        "Coffee Table -> table",
        "Sideboard / Side Cabinet / Console Table -> cabinet",
        "armchair -> chair",
        "Lounge Chair -> chair",
        "Loveseat Sofa / L-shaped Sofa / Multi-seat Sofa -> sofa",
        "Bookshelf / Shelf -> bookshelf",
        "TV Stand -> tv_stand",
        "Pendant Lamp -> pendant_lamp",
        "Ceiling Lamp -> ceiling_lamp",
    ]

    unsafe_mapping_rows = []
    for rule in mapping.get("rules", []):
        raw = str(rule.get("raw_category") or "")
        ref = str(rule.get("reference_category") or "")
        lo = str(rule.get("loreflection_category") or "")
        kind = unsafe_alias_kind(raw, ref, lo)
        if kind:
            unsafe_counts[f"mapping_{kind}"] += 1
            unsafe_mapping_rows.append(
                {
                    "raw_category": raw,
                    "reference_category": ref,
                    "loreflection_category": lo,
                    "unsafe_kind": kind,
                    "match_any": rule.get("match_any", []),
                }
            )

    sofa_to_chair_count = unsafe_counts["sofa_to_chair"] + unsafe_counts["mapping_sofa_to_chair"]
    table_to_desk_count = unsafe_counts["table_to_desk"] + unsafe_counts["mapping_table_to_desk"]
    unsafe_alias_count = sofa_to_chair_count + table_to_desk_count

    report = {
        "schema_version": "palette-alias-audit-v1",
        "prototype_root": args.prototype_root.as_posix(),
        "manifest_sample_count": len(manifest.get("samples", [])),
        "palette_alias_used_count": sum(row["count"] for row in alias_rows),
        "conversion_report_palette_alias_used_count": conversion.get("semantic_layout", {}).get("palette_alias_used_count"),
        "alias_rows": alias_rows,
        "remaining_alias_rows": alias_rows,
        "sofa_to_chair_count": sofa_to_chair_count,
        "table_to_desk_count": table_to_desk_count,
        "unsafe_alias_count": unsafe_alias_count,
        "unsafe_entity_rows": unsafe_entity_rows,
        "unsafe_mapping_rows": unsafe_mapping_rows,
        "alias_summary_by_loreflection_category": dict(summary_by_loreflection.most_common()),
        "alias_summary_by_reason": dict(summary_by_reason.most_common()),
        "recommended_palette_updates": recommended_updates,
        "must_review_before_scale50": must_review,
        "expected_aliases_checked": expected_aliases,
        "palette_categories": sorted(palette_colors.keys()),
        "mapping_rule_count": len(mapping.get("rules", [])),
    }
    write_json(args.output, report)
    if args.verbose:
        print(json.dumps(
            {
                "palette_alias_used_count": report["palette_alias_used_count"],
                "unsafe_alias_count": unsafe_alias_count,
                "sofa_to_chair_count": sofa_to_chair_count,
                "table_to_desk_count": table_to_desk_count,
                "alias_rows": alias_rows,
                "unsafe_mapping_rows": unsafe_mapping_rows,
                "recommended_palette_updates": recommended_updates,
                "must_review_before_scale50": must_review,
                "output": args.output.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        ))
    print(f"Wrote palette alias audit to {args.output}")
    if unsafe_alias_count:
        print(f"Unsafe palette aliases found: {unsafe_alias_count}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
