from __future__ import annotations

import argparse
import csv
import json
import shutil
from PIL import Image
import numpy as np
from collections import Counter
from pathlib import Path
from typing import Any

from loreflection.qwen_arch_control.prompt_labels.prompt_compiler_v2 import compile_prompt_package_v2
from loreflection.qwen_arch_control.raw_3dfront_adapter import collect_room_child_openings_sem_layoutdiff_style
from loreflection.qwen_arch_control.prompt_labels.relation_geometry_validator import validate_pairwise_constraints_against_target
from loreflection.qwen_arch_control.semantic_topdown_renderer import render_full_semantic_target_image
from loreflection.semantic_registry import load_registry

ARCHITECTURE_CONTROL_PROMPT = (
    "Architecture_Control. Follow the architecture condition image for room boundary, walls, doors, "
    "windows, clearance regions, and non-placeable regions."
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else base / p


def _find_source_meta(sample_id: str, suffix: str, roots: list[Path]) -> Path | None:
    name = f"{sample_id}_{suffix}.json"
    for root in roots:
        p = root / "meta" / name
        if p.exists():
            return p
    return None


def _required_counts_from_layout(layout: dict) -> dict[str, int]:
    return dict(Counter(str(o.get("category")) for o in layout.get("objects", []) if o.get("category")))


def build_user_intent(goal: dict) -> str:
    room_type = goal.get("room_type") or "room"
    required_counts = goal.get("required_counts") or {}
    parts = [f"{count} {category}" for category, count in sorted(required_counts.items())]
    item_text = ", ".join(parts) if parts else "the required semantic categories"
    relation_phrases = []
    for rel in goal.get("pairwise_constraints", []) or []:
        if rel.get("source") == "geometry_verified" and rel.get("prompt_allowed", True):
            relation_phrases.append(f"Keep {rel.get('subject')} {rel.get('predicate')} {rel.get('object')}.")
    relation_text = " " + " ".join(relation_phrases) if relation_phrases else ""
    return (
        f"Context_Control. Create a full semantic top-down {room_type} layout with {item_text}. "
        "Follow the architecture condition image and keep all objects inside valid room regions."
        f"{relation_text}"
    )


def _compile_prompt(user_prompt: str, goal: dict[str, Any], prompt_package: dict[str, Any], c2rgb_path: Path, *, source_prompt_package: str | None = None, goal_lostate_ref: str | None = None) -> dict:
    return compile_prompt_package_v2(
        user_intent_prompt=user_prompt,
        goal_lostate=goal,
        prompt_package=prompt_package,
        c2rgb_path=c2rgb_path,
        source_prompt_package=source_prompt_package,
        goal_lostate_ref=goal_lostate_ref,
    )


def _scene_room(scene: dict[str, Any], room_index: int) -> dict[str, Any] | None:
    rooms = (scene.get("scene") or {}).get("room") or (scene.get("scene") or {}).get("rooms") or []
    if isinstance(rooms, list) and 0 <= room_index < len(rooms) and isinstance(rooms[room_index], dict):
        return rooms[room_index]
    return None


def _apply_room_child_openings(architecture: dict[str, Any], scene_cache: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    architecture = json.loads(json.dumps(architecture))
    source = architecture.get("source") or {}
    scene_path = Path(source.get("source_scene_json") or "")
    room_index = int(source.get("room_index") if source.get("room_index") is not None else str(architecture.get("architecture_id", "")).rsplit("_room_", 1)[-1])
    key = str(scene_path)
    if key not in scene_cache:
        scene_cache[key] = _load_json(scene_path)
    scene = scene_cache[key]
    room = _scene_room(scene, room_index)
    if room is None:
        anchors = []
    else:
        anchors = collect_room_child_openings_sem_layoutdiff_style(scene, room, assigned_room_id=str(architecture.get("architecture_id") or ""))
    door_count = sum(1 for a in anchors if a.get("anchor_type") == "door")
    window_count = sum(1 for a in anchors if a.get("anchor_type") == "window")
    architecture.update({
        "anchors": anchors,
        "opening_source_policy": "semlayoutdiff_room_children_only",
        "door_anchor_count": door_count,
        "window_anchor_count": window_count,
        "native_room_child_door_count": door_count,
        "native_room_child_window_count": window_count,
        "has_room_child_door": door_count > 0,
        "has_room_child_window": window_count > 0,
    })
    return architecture, {"door_anchor_count": door_count, "window_anchor_count": window_count, "source_scene_json": str(scene_path), "room_index": room_index}


def build_dataset(source_root: Path, output_root: Path, *, limit: int | None = None, require_room_child_door: bool = True) -> dict:
    registry = load_registry()
    c2rgb_path = Path("artifacts/semantic_registry_v2/palette_frozen.json")
    source_rows = list(csv.DictReader((source_root / "metadata.csv").open(newline="", encoding="utf-8")))
    if limit:
        source_rows = source_rows[:limit]
    output_root.mkdir(parents=True, exist_ok=True)
    for sub in ["cond", "target_full_semantic", "meta"]:
        (output_root / sub).mkdir(parents=True, exist_ok=True)

    source_meta_roots = [
        source_root,
        Path("data/loreflection_qwen_arch_control_full_metric_v2"),
        Path("data/loreflection_qwen_arch_control_p1_small_metric_v2"),
        Path("data/loreflection_qwen_arch_control_p1_small"),
    ]
    rows: list[dict[str, str]] = []
    skipped: list[dict] = []
    scene_cache: dict[str, dict[str, Any]] = {}
    skip_counts: Counter[str] = Counter()
    for row in source_rows:
        sid = row["sample_id"]
        arch_src = _find_source_meta(sid, "architecture", source_meta_roots)
        layout_src = _find_source_meta(sid, "layout", source_meta_roots)
        manifest_src = _find_source_meta(sid, "sample_manifest", source_meta_roots)
        if not arch_src or not layout_src:
            skipped.append({"sample_id": sid, "reason": "missing_architecture_or_layout"})
            skip_counts["missing_architecture_or_layout"] += 1
            continue
        architecture = _load_json(arch_src)
        architecture, opening_report = _apply_room_child_openings(architecture, scene_cache)
        if require_room_child_door and not architecture.get("has_room_child_door"):
            skipped.append({"sample_id": sid, "reason": "drop_no_room_child_door_anchor", **opening_report})
            skip_counts["drop_no_room_child_door_anchor"] += 1
            continue
        layout = _load_json(layout_src)
        required_counts = _required_counts_from_layout(layout)
        goal = _load_json(_resolve(source_root, row["goal_lostate"])) if row.get("goal_lostate") else {}
        goal["sample_id"] = sid
        goal["required_counts"] = required_counts
        allowed_constraints = []
        dropped_constraints = []
        for constraint in goal.get("pairwise_constraints", []) or []:
            if constraint.get("source") == "geometry_verified" and constraint.get("prompt_allowed", True):
                allowed_constraints.append(constraint)
            else:
                dropped = dict(constraint)
                dropped["prompt_allowed"] = False
                dropped.setdefault("reason", "not_geometry_verified")
                dropped_constraints.append(dropped)
        goal["pairwise_constraints"] = allowed_constraints
        goal["dropped_pairwise_constraints"] = dropped_constraints
        goal["qwen_generates_full_semantic"] = True

        rel_context = Path("cond") / f"{sid}_arch_condition.png"
        rel_target = Path("target_full_semantic") / f"{sid}_target_full_semantic.png"
        _, render_report = render_full_semantic_target_image(
            architecture,
            layout,
            output_root / rel_target,
            context_output_path=output_root / rel_context,
            registry=registry,
        )
        if render_report["zero_written_object_count"]:
            skipped.append({"sample_id": sid, "reason": "zero_written_object", "count": render_report["zero_written_object_count"]})
            skip_counts["zero_written_object"] += 1
            (output_root / rel_context).unlink(missing_ok=True)
            (output_root / rel_target).unlink(missing_ok=True)
            continue
        missing_target_categories = _target_missing_required_categories(output_root / rel_target, required_counts, registry.palette)
        if missing_target_categories:
            skipped.append({"sample_id": sid, "reason": "drop_target_missing_required_category", "missing_categories": missing_target_categories})
            skip_counts["drop_target_missing_required_category"] += 1
            (output_root / rel_context).unlink(missing_ok=True)
            (output_root / rel_target).unlink(missing_ok=True)
            continue

        goal_rel = Path("meta") / f"{sid}_goal_lostate_geometry_verified.json"
        prompt_pkg_rel = Path("meta") / f"{sid}_compiled_prompt_package.json"
        verifier_rel = Path("meta") / f"{sid}_verifier_refs.json"
        relation_rel = Path("meta") / f"{sid}_relation_alignment_report.json"
        arch_rel = Path("meta") / f"{sid}_architecture.json"
        layout_rel = Path("meta") / f"{sid}_layout.json"
        manifest_rel = Path("meta") / f"{sid}_sample_manifest.json"
        _write_json(output_root / goal_rel, goal)
        _write_json(output_root / arch_rel, architecture)
        shutil.copy2(layout_src, output_root / layout_rel)
        if manifest_src and manifest_src.exists():
            shutil.copy2(manifest_src, output_root / manifest_rel)

        source_prompt_package = _resolve(source_root, row["prompt_package"])
        source_prompt_package_dict = _load_json(source_prompt_package) if source_prompt_package.exists() else {}
        user_prompt = build_user_intent(goal)
        prompt_package = _compile_prompt(user_prompt, goal, source_prompt_package_dict, c2rgb_path, source_prompt_package=str(source_prompt_package), goal_lostate_ref=str(goal_rel))
        prompt_package["architecture_control_prompt"] = ARCHITECTURE_CONTROL_PROMPT
        prompt_package["compiled_prompt"] = "\n\n".join([
            prompt_package.get("user_intent_prompt") or build_user_intent(goal),
            prompt_package["architecture_control_prompt"],
            prompt_package.get("palette_control_prompt") or "",
        ]).strip()
        prompt_package["sample_id"] = sid
        prompt_package["required_counts"] = required_counts
        prompt_package["render_report"] = render_report
        prompt_package["qwen_target_kind"] = "full_semantic"
        prompt_package["prompt_source"] = "goal_lostate_required_counts_geometry_verified_constraints"
        prompt_package["prompt_not_generated_from_images"] = True
        _write_json(output_root / prompt_pkg_rel, prompt_package)

        relation_report = validate_pairwise_constraints_against_target(
            goal.get("pairwise_constraints", []),
            layout_json=layout,
            target_full_semantic_path=output_root / rel_target,
        )
        _write_json(output_root / relation_rel, relation_report)
        verifier = {
            "schema_version": "verifier-refs-v1",
            "sample_id": sid,
            "architecture_json": str(arch_rel),
            "layout_json": str(layout_rel),
            "relation_alignment_report": str(relation_rel),
            "target_full_semantic": str(rel_target),
            "render_report": render_report,
        }
        _write_json(output_root / verifier_rel, verifier)
        rows.append({
            "image": str(rel_target),
            "prompt": prompt_package["compiled_prompt"],
            "context_image": str(rel_context),
            "sample_id": sid,
            "goal_lostate": str(goal_rel),
            "prompt_package": str(prompt_pkg_rel),
            "verifier_refs": str(verifier_rel),
        })

    with (output_root / "metadata.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"])
        writer.writeheader()
        writer.writerows(rows)
    summary = {"source_root": str(source_root), "output_root": str(output_root), "num_rows": len(rows), "num_skipped": len(skipped), "skip_counts": dict(skip_counts), "require_room_child_door": require_room_child_door, "opening_source_policy": "semlayoutdiff_room_children_only", "metadata_columns": ["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"], "skipped": skipped[:100]}
    _write_json(output_root / "build_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled")
    parser.add_argument("--output-root", default="data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled_next")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--allow-no-door", action="store_true", help="Keep rooms without room-child Door anchors. Default drops them.")
    args = parser.parse_args()
    print(json.dumps(build_dataset(Path(args.source_root), Path(args.output_root), limit=args.limit, require_room_child_door=not args.allow_no_door), indent=2))


if __name__ == "__main__":
    main()
