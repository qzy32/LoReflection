#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loreflection.qwen_arch_control.render_full_semantic_target import compose_full_semantic_target
from loreflection.qwen_arch_control.prompt_labels.prompt_compiler_v2 import compile_prompt_package_v2
from loreflection.qwen_arch_control.prompt_labels.relation_geometry_validator import (
    validate_pairwise_constraints_against_target,
)
from loreflection.semantic_registry import load_registry


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _count_phrase(count: int, category: str) -> str:
    return f"{count} {category}" if count == 1 else f"{count} {category}"


def build_user_intent(goal: dict[str, Any]) -> str:
    counts = {k: int(v) for k, v in goal.get("required_counts", {}).items() if int(v) > 0}
    room_type = goal.get("room_type") or "room"
    items = [_count_phrase(count, category) for category, count in sorted(counts.items())]
    if len(items) > 1:
        item_text = ", ".join(items[:-1]) + ", and " + items[-1]
    elif items:
        item_text = items[0]
    else:
        item_text = "the required furniture"
    parts = [
        f"Context_Control. Place {item_text} in the {room_type}.",
    ]
    relation_texts = []
    for rel in goal.get("pairwise_constraints", []):
        if not rel.get("prompt_allowed"):
            continue
        pred = rel.get("predicate")
        if pred in {"near", "closely_near"}:
            relation_texts.append(f"Keep {rel['subject']} near {rel['object']}.")
        elif pred == "around":
            relation_texts.append(f"Arrange {rel['subject']} around {rel['object']}.")
    parts.extend(relation_texts)
    parts.append("Keep all furniture inside the room, avoid overlap, and do not block doors or windows.")
    return " ".join(parts)


def _visible_furniture_categories(path: Path) -> set[str]:
    registry = load_registry()
    arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    visible = set()
    for sid in registry.object_ids:
        category = registry.id_to_name[sid]
        color = np.asarray(registry.id_to_rgb[sid], dtype=np.uint8)
        if np.all(arr == color, axis=-1).any():
            visible.add(category)
    return visible


def _visible_structural_categories(path: Path) -> set[str]:
    registry = load_registry()
    structural = {"floor", "wall", "door", "window", "clearance", "non_placeable", "room_mask"}
    arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    visible = set()
    for cat in registry.categories:
        if cat.name not in structural:
            continue
        color = np.asarray(cat.rgb, dtype=np.uint8)
        if np.all(arr == color, axis=-1).any():
            visible.add(cat.name)
    return visible


def build_dataset(
    *,
    source_dataset_root: Path,
    source_metadata: Path,
    output_root: Path,
    c2rgb_path: Path,
    sample_limit: int = 0,
) -> dict[str, Any]:
    rows = list(csv.DictReader(source_metadata.open(encoding="utf-8")))
    if sample_limit:
        rows = rows[:sample_limit]
    for sub in ["cond", "target_furniture_only", "target_full_semantic", "meta"]:
        (output_root / sub).mkdir(parents=True, exist_ok=True)

    out_rows: list[dict[str, str]] = []
    relation_invalid_count = 0
    skipped_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        sample_id = row["sample_id"]
        context_src = _resolve(source_dataset_root, row["context_image"])
        furniture_src = _resolve(source_dataset_root, row["image"])
        layout_path = source_dataset_root / "meta" / f"{sample_id}_layout.json"
        if not layout_path.exists():
            # prompt-label datasets reference the base metric-v2 package via ../
            base_root = source_dataset_root.parent / "loreflection_qwen_arch_control_p1_small_metric_v2"
            layout_path = base_root / "meta" / f"{sample_id}_layout.json"
        source_goal_path = _resolve(source_dataset_root, row["goal_lostate"])
        source_prompt_package_path = _resolve(source_dataset_root, row["prompt_package"])
        verifier_src = _resolve(source_dataset_root, row["verifier_refs"])

        cond_rel = Path("cond") / f"{sample_id}_arch_condition.png"
        furn_rel = Path("target_furniture_only") / f"{sample_id}_target_furniture_only.png"
        full_rel = Path("target_full_semantic") / f"{sample_id}_target_full_semantic.png"
        shutil.copy2(context_src, output_root / cond_rel)
        shutil.copy2(furniture_src, output_root / furn_rel)
        full_report = compose_full_semantic_target(
            context_image_path=output_root / cond_rel,
            furniture_target_path=output_root / furn_rel,
            output_path=output_root / full_rel,
        )
        if float(full_report.get("forbidden_architecture_overwrite_rate", 0.0)) > 0.001:
            skipped_rows.append(
                {
                    "sample_id": sample_id,
                    "reason": "forbidden_architecture_overwrite",
                    "forbidden_architecture_overwrite_rate": full_report.get("forbidden_architecture_overwrite_rate"),
                }
            )
            continue
        if not _visible_structural_categories(output_root / full_rel):
            skipped_rows.append({"sample_id": sample_id, "reason": "no_structural_architecture_pixels_in_full_target"})
            continue

        goal = _read_json(source_goal_path)
        prompt_package = _read_json(source_prompt_package_path) if source_prompt_package_path.exists() else {}
        layout = _read_json(layout_path) if layout_path.exists() else {}
        visible_categories = _visible_furniture_categories(output_root / furn_rel)
        original_counts = {k: int(v) for k, v in goal.get("required_counts", {}).items() if int(v) > 0}
        filtered_counts = {k: v for k, v in original_counts.items() if k in visible_categories}
        dropped_required_counts = [
            {"category": k, "count": v, "reason": "not_visible_in_target_pixels", "prompt_allowed": False}
            for k, v in sorted(original_counts.items())
            if k not in visible_categories
        ]
        candidate_relations = [
            rel
            for rel in goal.get("pairwise_constraints", [])
            if rel.get("subject") in filtered_counts and rel.get("object") in filtered_counts
        ]
        relation_category_drops = [
            {**rel, "reason": "relation_category_not_visible_in_target_pixels", "prompt_allowed": False}
            for rel in goal.get("pairwise_constraints", [])
            if rel.get("subject") not in filtered_counts or rel.get("object") not in filtered_counts
        ]
        validation = validate_pairwise_constraints_against_target(
            candidate_relations,
            layout_json=layout,
            target_furniture_only_path=output_root / furn_rel,
        )
        validation["dropped"].extend(relation_category_drops)
        relation_invalid_count += len(validation["dropped"])
        fixed_goal = dict(goal)
        fixed_goal["required_counts"] = filtered_counts
        fixed_goal["furniture_slots"] = [
            slot for slot in goal.get("furniture_slots", []) if slot.get("category") in filtered_counts
        ]
        fixed_goal["pairwise_constraints"] = validation["geometry_verified"]
        fixed_goal["dropped_pairwise_constraints"] = validation["dropped"]
        fixed_goal["dropped_required_counts"] = dropped_required_counts
        fixed_goal["relation_validation_source"] = validation["validation_source"]
        user_intent = build_user_intent(fixed_goal)
        compiler_input = {
            **prompt_package,
            "geometry_verified_constraints": validation["geometry_verified"],
            "dropped_constraints": validation["dropped"],
        }
        goal_rel = Path("meta") / f"{sample_id}_goal_lostate_geometry_verified.json"
        prompt_rel = Path("meta") / f"{sample_id}_compiled_prompt_package.json"
        relation_rel = Path("meta") / f"{sample_id}_relation_alignment_report.json"
        verifier_rel = Path("meta") / f"{sample_id}_verifier_refs.json"
        compiled = compile_prompt_package_v2(
            user_intent_prompt=user_intent,
            goal_lostate=fixed_goal,
            prompt_package=compiler_input,
            c2rgb_path=c2rgb_path,
            source_prompt_package=row["prompt_package"],
            goal_lostate_ref=goal_rel.as_posix(),
        )
        (output_root / goal_rel).write_text(json.dumps(fixed_goal, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_root / prompt_rel).write_text(json.dumps(compiled, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_root / relation_rel).write_text(
            json.dumps({"sample_id": sample_id, **validation, "full_semantic_report": full_report}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if verifier_src.exists():
            shutil.copy2(verifier_src, output_root / verifier_rel)
        else:
            (output_root / verifier_rel).write_text(json.dumps({"sample_id": sample_id}, indent=2), encoding="utf-8")
        out_rows.append(
            {
                "image": full_rel.as_posix(),
                "prompt": compiled["compiled_prompt"],
                "context_image": cond_rel.as_posix(),
                "target_furniture_only": furn_rel.as_posix(),
                "target_full_semantic": full_rel.as_posix(),
                "sample_id": sample_id,
                "goal_lostate": goal_rel.as_posix(),
                "prompt_package": prompt_rel.as_posix(),
                "verifier_refs": verifier_rel.as_posix(),
            }
        )

    metadata = output_root / "metadata.csv"
    with metadata.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image",
                "prompt",
                "context_image",
                "target_furniture_only",
                "target_full_semantic",
                "sample_id",
                "goal_lostate",
                "prompt_package",
                "verifier_refs",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)
    result = {
        "output_root": str(output_root),
        "metadata": str(metadata),
        "num_rows": len(out_rows),
        "num_source_rows": len(rows),
        "num_skipped_rows": len(skipped_rows),
        "skipped_rows": skipped_rows[:200],
        "relation_invalid_count": relation_invalid_count,
        "status": "built",
    }
    (output_root / "build_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dataset-root", type=Path, required=True)
    parser.add_argument("--source-metadata", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--c2rgb-path", type=Path, default=Path("artifacts/semantic_registry_v2/palette_frozen.json"))
    parser.add_argument("--sample-limit", type=int, default=0)
    args = parser.parse_args()
    result = build_dataset(
        source_dataset_root=args.source_dataset_root,
        source_metadata=args.source_metadata,
        output_root=args.output_root,
        c2rgb_path=args.c2rgb_path,
        sample_limit=args.sample_limit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
