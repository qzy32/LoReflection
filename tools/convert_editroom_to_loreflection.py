#!/usr/bin/env python
"""Convert EditRoom-like toy edit pairs into LoReflection Planner SFT and repair samples."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(REPO_ROOT))

from build_mask_spec_from_editroom_pair import build_mask_spec, load_json, objects_by_id
from build_repairplan_from_editroom_pair import build_repairplan
from runtime.mask_tensor_adapter import rasterize_mask_spec


def load_palette() -> dict:
    return load_json(REPO_ROOT / "configs" / "palette_v1.json")["colors"]


def render_layout(layout: dict, output: Path) -> None:
    """Render a toy layout JSON into a fixed-palette semantic PNG."""
    palette = load_palette()
    width, height = layout.get("image_size_px", [1024, 1024])
    image = Image.new("RGB", (width, height), palette.get("floor", "#F4F1E8"))
    draw = ImageDraw.Draw(image)
    draw.rectangle([24, 24, width - 24, height - 24], outline=palette.get("wall", "#202020"), width=8)
    for obj in layout.get("objects", []):
        color = palette.get(obj.get("category"), "#888888")
        draw.rectangle([int(v) for v in obj["bbox_px"]], fill=color)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def find_edit_dirs(input_root: Path) -> list[Path]:
    if (input_root / "before_layout.json").exists():
        return [input_root]
    return sorted(
        path
        for path in input_root.iterdir()
        if path.is_dir()
        and (path / "before_layout.json").exists()
        and (path / "after_layout.json").exists()
        and (path / "edit_instruction.json").exists()
    )


def build_observed_lostate(before: dict, instruction: dict, source_image: str) -> dict:
    return {
        "schema_version": "observed-lostate-v1",
        "state_role": "observed",
        "metadata": {"task_id": instruction["edit_id"], "repair_round": 0, "source_image": source_image},
        "architecture_ref": {"architecture_id": f"editroom_arch_{instruction['edit_id']}"},
        "semantic_registry_ref": {"palette_id": "indoor_palette_v1", "category_set": "indoor_furniture_categories_v1", "relation_set": "layout_relations_v1"},
        "room_type": instruction.get("room_type", before.get("room_type", "room")),
        "furniture_instances": [
            {
                "instance_id": obj["instance_id"],
                "category": obj["category"],
                "bbox_px": obj["bbox_px"],
            }
            for obj in before.get("objects", [])
        ],
        "measured_relations": [],
        "hard_constraint_evidence": [],
    }


def build_goal_lostate(after: dict, instruction: dict) -> dict:
    relation = instruction.get("target_relation", {})
    slots = [
        {
            "slot_id": obj["instance_id"],
            "category": obj["category"],
            "required": True,
            "count": 1,
            "source": "editroom_after_layout",
        }
        for obj in after.get("objects", [])
    ]
    relations = []
    if relation:
        relations.append(
            {
                "relation_id": f"edit_rel_{instruction['edit_id']}",
                "subject": instruction.get("target_ref", instruction.get("target_category", "target")),
                "predicate": relation.get("predicate", "near"),
                "object": relation.get("object", "reference_object"),
                "object_kind": "observed_instance",
                "necessity": "required",
                "verification": "geometric_then_semantic",
                "source": "editroom_instruction",
            }
        )
    return {
        "schema_version": "goal-lostate-v1",
        "state_role": "goal",
        "metadata": {"task_id": instruction["edit_id"], "repair_round": 0, "created_by": "EditRoom toy adapter"},
        "architecture_ref": {"architecture_id": f"editroom_arch_{instruction['edit_id']}"},
        "semantic_registry_ref": {"palette_id": "indoor_palette_v1", "category_set": "indoor_furniture_categories_v1", "relation_set": "layout_relations_v1"},
        "room_type": instruction.get("room_type", after.get("room_type", "room")),
        "furniture_slots": slots,
        "desired_relations": relations,
        "verification_profile": {"hard_checks": []},
    }


def build_loreview(before: dict, after: dict, instruction: dict, repairplan: dict) -> dict:
    edit_type = instruction["edit_type"].upper()
    issue_type = {
        "INSERT": "entity_missing",
        "DELETE": "entity_extra",
        "REPLACE": "category_mismatch",
        "MOVE": "relation_violation",
    }[edit_type]
    before_ids = set(objects_by_id(before))
    after_ids = set(objects_by_id(after))
    alignment = []
    for instance_id in sorted(before_ids | after_ids):
        alignment.append(
            {
                "slot_id": instance_id if instance_id in after_ids else None,
                "instance_id": instance_id if instance_id in before_ids else None,
                "match_type": "exact" if instance_id in before_ids and instance_id in after_ids else ("missing" if instance_id in after_ids else "extra"),
            }
        )
    issue = {
        "issue_id": f"{issue_type}_{instruction['edit_id']}",
        "issue_type": issue_type,
        "severity": "error" if edit_type in {"INSERT", "MOVE", "REPLACE"} else "warning",
        "target_ref": repairplan["target_ref"],
        "recommended_action_type": repairplan["action_type"],
        "track": "A",
    }
    return {
        "schema_version": "loreview-v1",
        "review_id": f"loreview_{instruction['edit_id']}",
        "task_id": instruction["edit_id"],
        "repair_round": 0,
        "alignment": alignment,
        "issues": [issue],
        "summary": {"num_issues": 1, "num_hard": 1 if issue["severity"] == "error" else 0},
    }


def rel(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def convert_toy(input_root: Path, output_root: Path) -> dict:
    dirs = {
        "planner": output_root / "planner_sft_v1",
        "controlnet": output_root / "controlnet_repair_v1",
        "masks": output_root / "masks",
        "images": output_root / "images",
        "targets": output_root / "targets",
        "repairplans": output_root / "repairplans",
        "reports": output_root / "reports",
        "contexts": output_root / "planner_sft_v1" / "contexts",
        "mask_specs": output_root / "masks" / "specs",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": "editroom-conversion-report-v1",
        "input_root": str(input_root),
        "output_root": str(output_root),
        "mode": "toy",
        "total_pairs": 0,
        "converted_pairs": 0,
        "failed_pairs": [],
        "warnings": [],
    }
    planner_samples = []
    controlnet_samples = []
    edit_dirs = find_edit_dirs(input_root)
    report["total_pairs"] = len(edit_dirs)
    if not edit_dirs:
        report["warnings"].append("No EditRoom-like toy pairs found.")

    for edit_dir in edit_dirs:
        sample_id = edit_dir.name
        try:
            before = load_json(edit_dir / "before_layout.json")
            after = load_json(edit_dir / "after_layout.json")
            instruction = load_json(edit_dir / "edit_instruction.json")
            edit_id = instruction.get("edit_id", sample_id)
            before_image = dirs["images"] / f"{edit_id}_before.png"
            after_image = dirs["targets"] / f"{edit_id}_after.png"
            render_layout(before, before_image)
            render_layout(after, after_image)

            mask_spec = build_mask_spec(before, after, instruction)
            mask_spec_path = dirs["mask_specs"] / f"{edit_id}_mask_spec.json"
            mask_spec_path.write_text(json.dumps(mask_spec, ensure_ascii=False, indent=2), encoding="utf-8")
            control_mask_path = dirs["masks"] / f"{edit_id}_control_mask.png"
            rasterize_mask_spec(mask_spec, build_observed_lostate(before, instruction, str(before_image)), None).save(control_mask_path)

            repairplan = build_repairplan(before, after, instruction, mask_spec)
            repairplan_path = dirs["repairplans"] / f"{edit_id}_repairplan.json"
            repairplan_path.write_text(json.dumps(repairplan, ensure_ascii=False, indent=2), encoding="utf-8")

            goal_path = dirs["contexts"] / f"{edit_id}_goal_lostate.json"
            observed_path = dirs["contexts"] / f"{edit_id}_observed_lostate.json"
            loreview_path = dirs["contexts"] / f"{edit_id}_loreview.json"
            goal_path.write_text(json.dumps(build_goal_lostate(after, instruction), ensure_ascii=False, indent=2), encoding="utf-8")
            observed_path.write_text(json.dumps(build_observed_lostate(before, instruction, rel(before_image, output_root)), ensure_ascii=False, indent=2), encoding="utf-8")
            loreview_path.write_text(json.dumps(build_loreview(before, after, instruction, repairplan), ensure_ascii=False, indent=2), encoding="utf-8")

            planner_samples.append(
                {
                    "sample_id": edit_id,
                    "image": rel(before_image, dirs["planner"]),
                    "instruction": instruction.get("instruction", ""),
                    "goal_lostate": rel(goal_path, dirs["planner"]),
                    "observed_lostate": rel(observed_path, dirs["planner"]),
                    "loreview": rel(loreview_path, dirs["planner"]),
                    "repairplan": rel(repairplan_path, dirs["planner"]),
                    "edit_type": instruction["edit_type"].upper(),
                }
            )
            mask_type = mask_spec["items"][0]["type"]
            controlnet_samples.append(
                {
                    "schema_version": "controlnet-sample-v1",
                    "sample_id": edit_id,
                    "control_image": rel(before_image, output_root),
                    "control_mask": rel(control_mask_path, output_root),
                    "target_image": rel(after_image, output_root),
                    "correction_prompt": repairplan["correction_prompt"],
                    "prompt": repairplan["correction_prompt"],
                    "edit_type": instruction["edit_type"].upper(),
                    "mask_type": mask_type,
                    "repairplan_path": rel(repairplan_path, output_root),
                    "repair_plan": rel(repairplan_path, output_root),
                    "split": instruction.get("split", "train"),
                }
            )
            report["converted_pairs"] += 1
        except Exception as exc:
            report["failed_pairs"].append({"sample_id": sample_id, "error": str(exc)})

    (dirs["planner"] / "planner_sft_manifest.json").write_text(
        json.dumps({"schema_version": "planner-sft-manifest-v1", "samples": planner_samples}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (dirs["controlnet"] / "train.json").write_text(
        json.dumps({"schema_version": "controlnet-repair-manifest-v1", "samples": controlnet_samples}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (dirs["reports"] / "editroom_conversion_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def validate_output(output_root: Path) -> None:
    subprocess.run([sys.executable, "tools/validate_all.py", "--data-root", str(output_root), "--strict"], cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", required=True, type=Path, help="EditRoom-like toy input root.")
    parser.add_argument("--output-root", required=True, type=Path, help="Output root for LoReflection artifacts.")
    parser.add_argument("--mode", required=True, choices=["toy"], help="Conversion mode. Only toy is implemented locally.")
    args = parser.parse_args()
    # TODO(server): add real EditRoom modes after inspecting upstream pair manifests.
    report = convert_toy(args.input_root, args.output_root)
    validate_output(args.output_root)
    print(f"Wrote EditRoom conversion report to {args.output_root / 'reports' / 'editroom_conversion_report.json'}")
    return 1 if report["failed_pairs"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
