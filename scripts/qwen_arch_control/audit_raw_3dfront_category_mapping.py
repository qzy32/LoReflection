#!/usr/bin/env python3
"""Audit raw 3D-FRONT -> LoReflection semantic category mapping."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loreflection.qwen_arch_control.raw_3dfront_adapter import (  # noqa: E402
    map_3dfuture_category_to_semlayoutdiff,
    normalize_room_type,
)
from loreflection.qwen_arch_control.source_resolver import (  # noqa: E402
    load_model_info_index,
    probe_data_root,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def _dataset_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _old_layout_categories(root: Path, row: dict[str, str]) -> dict[str, str]:
    refs = _load_json(_dataset_path(root, row["verifier_refs"]))
    layout = _load_json(_dataset_path(root, refs["layout_json"]))
    out: dict[str, str] = {}
    for obj in layout.get("objects", []):
        if isinstance(obj, dict) and obj.get("instance_id"):
            out[str(obj["instance_id"])] = str(obj.get("category") or "")
    return out


def _architecture_source(root: Path, row: dict[str, str]) -> tuple[Path, int, str]:
    refs = _load_json(_dataset_path(root, row["verifier_refs"]))
    arch = _load_json(_dataset_path(root, refs["architecture_json"]))
    source = arch.get("source") or {}
    return Path(source["source_scene_json"]), int(source["room_index"]), str(arch.get("room_type") or "")


def _forbidden_flags(raw_category: str, mapped_category: str | None) -> list[str]:
    text = raw_category.lower()
    flags = []
    if ("footstool" in text or "sofastool" in text) and mapped_category == "double_bed":
        flags.append("forbidden_footstool_to_double_bed")
    if "bed end stool" in text and mapped_category == "double_bed":
        flags.append("forbidden_bed_end_stool_to_double_bed")
    if "nightstand" in text and mapped_category == "desk":
        flags.append("forbidden_nightstand_to_desk")
    if "wardrobe" in text and mapped_category == "desk":
        flags.append("forbidden_wardrobe_to_desk")
    if ("bookcase" in text or "jewelry armoire" in text) and mapped_category == "desk":
        flags.append("forbidden_bookcase_to_desk")
    if text.strip() == "shelf" and mapped_category == "desk":
        flags.append("forbidden_shelf_to_desk")
    if "drawer chest" in text and mapped_category == "desk":
        flags.append("forbidden_drawer_chest_to_desk")
    return flags


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--data-root", default="/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front")
    parser.add_argument("--semlayoutdiff-root", default=None)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader((dataset_root / "metadata.csv").open("r", encoding="utf-8")))
    probe = probe_data_root(Path(args.data_root))
    model_index = load_model_info_index([Path(p) for p in probe["model_info_paths"]])

    scene_cache: dict[Path, dict[str, Any]] = {}
    summary = Counter()
    room_type_counts = Counter()
    legacy_forbidden = Counter()
    kept_sample_ids: set[str] = set()
    dropped_sample_ids: set[str] = set()
    livingroom_with_bed: set[str] = set()
    forbidden_new = []
    unknown_cases = []
    unsupported_cases = []

    jsonl_path = output_dir / "raw_mapping_audit_before_after.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as writer:
        for row in rows:
            sid = row["sample_id"]
            scene_path, room_index, old_arch_room_type = _architecture_source(dataset_root, row)
            if scene_path not in scene_cache:
                scene_cache[scene_path] = _load_json(scene_path)
            scene = scene_cache[scene_path]
            room = scene["scene"]["room"][room_index]
            raw_room_type = str(room.get("type") or "")
            normalized_room_type = normalize_room_type(raw_room_type)
            room_type_counts[raw_room_type] += 1
            summary["samples_scanned"] += 1

            if normalized_room_type is None:
                dropped_sample_ids.add(sid)
                unsupported_cases.append(
                    {
                        "sample_id": sid,
                        "raw_room_type": raw_room_type,
                        "old_arch_room_type": old_arch_room_type,
                        "drop_reason": "unsupported_room_type",
                    }
                )
            else:
                kept_sample_ids.add(sid)

            furniture_by_uid = {
                str(item.get("uid")): item
                for item in scene.get("furniture", [])
                if isinstance(item, dict) and item.get("uid") is not None
            }
            old_categories = _old_layout_categories(dataset_root, row)
            new_categories = []
            for child in room.get("children", []) if isinstance(room.get("children"), list) else []:
                if not isinstance(child, dict):
                    continue
                furniture = furniture_by_uid.get(str(child.get("ref")))
                if not furniture:
                    continue
                jid = str(furniture.get("jid") or "")
                model_info = model_index.get(jid) or {}
                raw_category = str(model_info.get("category") or "")
                raw_title = str(furniture.get("title") or furniture.get("name") or furniture.get("type") or "")
                super_category = str(model_info.get("super-category") or model_info.get("super_category") or "")
                result = map_3dfuture_category_to_semlayoutdiff(
                    raw_category,
                    raw_title=raw_title,
                    super_category=super_category,
                )
                instance_id = str(child.get("instanceid") or "")
                old_category = old_categories.get(instance_id)
                summary["objects_scanned"] += 1
                if result.category:
                    summary["objects_mapped"] += 1
                    new_categories.append(result.category)
                else:
                    summary["objects_dropped_unknown"] += 1
                    unknown_cases.append(
                        {
                            "sample_id": sid,
                            "instance_id": instance_id,
                            "jid": jid,
                            "raw_category": raw_category,
                            "raw_title": raw_title,
                            "super_category": super_category,
                            "confidence": result.confidence,
                        }
                    )
                if normalized_room_type is None:
                    summary["objects_dropped_unsupported_room"] += 1

                flags = _forbidden_flags(raw_category, result.category)
                for flag in flags:
                    summary[flag] += 1
                if flags:
                    forbidden_new.append(
                        {
                            "sample_id": sid,
                            "instance_id": instance_id,
                            "jid": jid,
                            "raw_category": raw_category,
                            "raw_title": raw_title,
                            "super_category": super_category,
                            "new_category": result.category,
                            "flags": flags,
                        }
                    )

                for flag in _forbidden_flags(raw_category, old_category):
                    legacy_forbidden["legacy_" + flag] += 1

                writer.write(
                    json.dumps(
                        {
                            "sample_id": sid,
                            "raw_room_type": raw_room_type,
                            "normalized_room_type": normalized_room_type,
                            "room_gate_status": "keep" if normalized_room_type else "drop_unsupported_room_type",
                            "instance_id": instance_id,
                            "uid": furniture.get("uid"),
                            "jid": jid,
                            "model_info_category": raw_category,
                            "model_info_super_category": super_category,
                            "title": raw_title,
                            "old_mapped_category": old_category,
                            "new_mapped_category": result.category,
                            "mapping_confidence": result.confidence,
                            "mapping_source": result.source,
                            "notes": result.notes,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            if normalized_room_type == "livingroom" and any(
                cat in {"double_bed", "single_bed", "kids_bed"} for cat in new_categories
            ):
                livingroom_with_bed.add(sid)

    forbidden_keys = [
        "forbidden_footstool_to_double_bed",
        "forbidden_bed_end_stool_to_double_bed",
        "forbidden_nightstand_to_desk",
        "forbidden_wardrobe_to_desk",
        "forbidden_bookcase_to_desk",
        "forbidden_shelf_to_desk",
        "forbidden_drawer_chest_to_desk",
        "super_category_triggered_primary_mapping_count",
    ]
    summary_dict = dict(summary)
    for key in forbidden_keys:
        summary_dict.setdefault(key, 0)
    summary_dict.update(dict(legacy_forbidden))
    summary_dict.update(
        {
            "dataset_root": str(dataset_root),
            "semlayoutdiff_root": args.semlayoutdiff_root,
            "samples_scanned": len(rows),
            "allowed_room_samples": len(kept_sample_ids),
            "dropped_room_samples": len(dropped_sample_ids),
            "livingroom_with_bed_count": len(livingroom_with_bed),
            "raw_room_type_histogram": dict(room_type_counts.most_common()),
            "status": "pass" if all(summary_dict.get(key, 0) == 0 for key in forbidden_keys) else "fail",
        }
    )

    (output_dir / "raw_mapping_audit_summary.json").write_text(
        json.dumps(summary_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "forbidden_mapping_cases.json").write_text(
        json.dumps(forbidden_new, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "unknown_mapping_cases.json").write_text(
        json.dumps(unknown_cases[:5000], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "unsupported_room_type_cases.json").write_text(
        json.dumps(unsupported_cases, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md = [
        "# Raw 3D-FRONT Category Mapping Audit",
        "",
        f"Dataset root: `{dataset_root}`",
        f"Samples scanned: {len(rows)}",
        f"Allowed room samples: {len(kept_sample_ids)}",
        f"Dropped room samples: {len(dropped_sample_ids)}",
        f"Objects scanned: {summary_dict.get('objects_scanned', 0)}",
        f"Objects mapped: {summary_dict.get('objects_mapped', 0)}",
        f"Objects dropped unknown: {summary_dict.get('objects_dropped_unknown', 0)}",
        "",
        "## New Forbidden Mapping Counts",
    ]
    for key in forbidden_keys:
        md.append(f"- {key}: {summary_dict.get(key, 0)}")
    md.extend(["", "## Legacy Polluted Mapping Counts"])
    for key, value in sorted(legacy_forbidden.items()):
        md.append(f"- {key}: {value}")
    md.extend(["", "## Room Type Histogram"])
    for room_type, count in room_type_counts.most_common():
        md.append(f"- {room_type}: {count}")
    md.extend(["", f"Status: `{summary_dict['status']}`", ""])
    (output_dir / "raw_mapping_audit_summary.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary_dict, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
