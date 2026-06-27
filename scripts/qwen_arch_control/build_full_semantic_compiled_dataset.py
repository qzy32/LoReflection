from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path

from loreflection.qwen_arch_control.prompt_labels.prompt_compiler_v2 import compile_prompt_package_v2
from loreflection.qwen_arch_control.prompt_labels.relation_geometry_validator import validate_pairwise_constraints_against_target
from loreflection.qwen_arch_control.semantic_topdown_renderer import render_full_semantic_target_image
from loreflection.semantic_registry import load_registry

ARCHITECTURE_CONTROL_PROMPT = (
    "Architecture_Control. Use the architecture condition image for the room floor region, room boundary, and doors/windows when visible. Keep all furniture inside floor pixels and avoid door/window areas."
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


def _compile_prompt(user_prompt: str, goal_path: Path, prompt_package_path: Path, c2rgb_path: Path) -> dict:
    return compile_prompt_package_v2(
        user_intent_prompt=user_prompt,
        goal_lostate_path=goal_path,
        prompt_package_path=prompt_package_path,
        c2rgb_path=c2rgb_path,
    )


def build_dataset(source_root: Path, output_root: Path, *, limit: int | None = None) -> dict:
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
    for row in source_rows:
        sid = row["sample_id"]
        arch_src = _find_source_meta(sid, "architecture", source_meta_roots)
        layout_src = _find_source_meta(sid, "layout", source_meta_roots)
        manifest_src = _find_source_meta(sid, "sample_manifest", source_meta_roots)
        if not arch_src or not layout_src:
            skipped.append({"sample_id": sid, "reason": "missing_architecture_or_layout"})
            continue
        architecture = _load_json(arch_src)
        layout = _load_json(layout_src)
        required_counts = _required_counts_from_layout(layout)
        goal = _load_json(_resolve(source_root, row["goal_lostate"])) if row.get("goal_lostate") else {}
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
            continue

        goal_rel = Path("meta") / f"{sid}_goal_lostate_geometry_verified.json"
        prompt_pkg_rel = Path("meta") / f"{sid}_compiled_prompt_package.json"
        verifier_rel = Path("meta") / f"{sid}_verifier_refs.json"
        relation_rel = Path("meta") / f"{sid}_relation_alignment_report.json"
        arch_rel = Path("meta") / f"{sid}_architecture.json"
        layout_rel = Path("meta") / f"{sid}_layout.json"
        manifest_rel = Path("meta") / f"{sid}_sample_manifest.json"
        _write_json(output_root / goal_rel, goal)
        shutil.copy2(arch_src, output_root / arch_rel)
        shutil.copy2(layout_src, output_root / layout_rel)
        if manifest_src and manifest_src.exists():
            shutil.copy2(manifest_src, output_root / manifest_rel)

        source_prompt_package = _resolve(source_root, row["prompt_package"])
        prompt_package = _compile_prompt(row["prompt"], output_root / goal_rel, source_prompt_package, c2rgb_path)
        prompt_package["architecture_control_prompt"] = ARCHITECTURE_CONTROL_PROMPT
        prompt_package["compiled_prompt"] = "\n\n".join([
            prompt_package.get("user_intent_prompt") or build_user_intent(goal),
            prompt_package["architecture_control_prompt"],
            prompt_package.get("palette_control_prompt") or "",
        ]).strip()
        prompt_package["render_report"] = render_report
        prompt_package["qwen_target_kind"] = "full_semantic"
        _write_json(output_root / prompt_pkg_rel, prompt_package)

        relation_report = validate_pairwise_constraints_against_target(
            constraints=goal.get("pairwise_constraints", []),
            layout_json_path=output_root / layout_rel,
            target_full_semantic_path=output_root / rel_target,
            architecture_json_path=output_root / arch_rel,
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
    summary = {"source_root": str(source_root), "output_root": str(output_root), "num_rows": len(rows), "num_skipped": len(skipped), "skipped": skipped[:100]}
    _write_json(output_root / "build_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled")
    parser.add_argument("--output-root", default="data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled_next")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(build_dataset(Path(args.source_root), Path(args.output_root), limit=args.limit), indent=2))


if __name__ == "__main__":
    main()
