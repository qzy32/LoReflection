#!/usr/bin/env python
"""Build a unified LoReflection toy package from local toy adapter outputs."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path


INTERFACE_TAG = "interface-freeze-v1"
SOURCE_TAGS = [
    "step2.2-semlayoutdiff-toy-pass",
    "step2.3-editroom-toy-pass-v2",
    "interface-freeze-v1",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_file(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst.as_posix()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def ensure_dirs(output_root: Path) -> dict[str, Path]:
    if output_root.exists():
        shutil.rmtree(output_root)
    dirs = {
        "arch_json": output_root / "arch_json_v1",
        "arch_condition": output_root / "arch_condition_v1",
        "gt_semantic": output_root / "gt_semantic_layout_v1",
        "goal": output_root / "goal_lostate_v1",
        "observed": output_root / "observed_lostate_v1",
        "loreview": output_root / "loreview_v1",
        "repairplans": output_root / "repairplans",
        "masks": output_root / "masks",
        "mask_specs": output_root / "masks" / "specs",
        "images": output_root / "images",
        "targets": output_root / "targets",
        "planner": output_root / "planner_sft_v1",
        "controlnet": output_root / "controlnet_repair_v1",
        "diffsynth": output_root / "diffsynth_inpaint_v1",
        "diffsynth_images": output_root / "diffsynth_inpaint_v1" / "images",
        "diffsynth_masks": output_root / "diffsynth_inpaint_v1" / "masks",
        "diffsynth_targets": output_root / "diffsynth_inpaint_v1" / "targets",
        "reports": output_root / "reports",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def convert_qwenvl_rows(planner_samples: list[dict], package_root: Path) -> list[dict]:
    rows = []
    for sample in planner_samples:
        repairplan = load_json(package_root / sample["repairplan"])
        parts = [
            "<image>",
            "[CORRECTION_PLANNING_WITH_MASK_PLAN]",
            "Given the current semantic layout image, Goal LoState, Observed LoState, and LoReview, output a RepairPlan JSON with mask_spec and correction_prompt.",
        ]
        for label, key in [
            ("Goal LoState", "goal_lostate"),
            ("Observed LoState", "observed_lostate"),
            ("LoReview", "loreview"),
        ]:
            parts.append(f"{label}:\n{json.dumps(load_json(package_root / sample[key]), ensure_ascii=False, indent=2)}")
        if sample.get("instruction"):
            parts.append(f"User instruction: {sample['instruction']}")
        rows.append(
            {
                "id": sample["sample_id"],
                "image": sample["image"],
                "conversations": [
                    {"from": "human", "value": "\n\n".join(parts)},
                    {"from": "gpt", "value": json.dumps(repairplan, ensure_ascii=False, indent=2)},
                ],
            }
        )
    return rows


def add_core_toy(toy_root: Path, output_root: Path, dirs: dict[str, Path], samples: list[dict], planner_samples: list[dict], controlnet_samples: list[dict], warnings: list[str]) -> None:
    sample_id = "toy_bedroom_001"
    required = {
        "architecture": toy_root / "architecture_v1.json",
        "arch_condition": toy_root / "arch_condition.png",
        "gt": toy_root / "target_layout.png",
        "control_image": toy_root / "bad_layout.png",
        "control_mask": toy_root / "control_mask.png",
        "goal": toy_root / "goal_lostate_v1.json",
        "observed": toy_root / "observed_from_image.json",
        "loreview": toy_root / "loreview_from_image.json",
        "repairplan": toy_root / "repairplan_v1.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        warnings.append(f"core toy sample skipped because files are missing: {missing}")
        return

    arch = Path(copy_file(required["architecture"], dirs["arch_json"] / f"{sample_id}.architecture_v1.json"))
    copy_file(required["arch_condition"], dirs["arch_condition"] / f"{sample_id}.arch_condition.png")
    copy_file(required["gt"], dirs["gt_semantic"] / f"{sample_id}.semantic_layout.png")
    control_image = Path(copy_file(required["control_image"], dirs["images"] / f"{sample_id}_control.png"))
    target_image = Path(copy_file(required["gt"], dirs["targets"] / f"{sample_id}_target.png"))
    control_mask = Path(copy_file(required["control_mask"], dirs["masks"] / f"{sample_id}_control_mask.png"))
    goal = Path(copy_file(required["goal"], dirs["goal"] / f"{sample_id}_goal_lostate.json"))
    observed = Path(copy_file(required["observed"], dirs["observed"] / f"{sample_id}_observed_lostate.json"))
    loreview = Path(copy_file(required["loreview"], dirs["loreview"] / f"{sample_id}_loreview.json"))
    repairplan = Path(copy_file(required["repairplan"], dirs["repairplans"] / f"{sample_id}_repairplan.json"))
    mask_spec = load_json(required["repairplan"]).get("mask_spec")
    if mask_spec:
        write_json(dirs["mask_specs"] / f"{sample_id}_mask_spec.json", mask_spec)

    planner_entry = {
        "sample_id": sample_id,
        "image": rel(control_image, output_root),
        "instruction": "Plan one local repair for the missing nightstand.",
        "goal_lostate": rel(goal, output_root),
        "observed_lostate": rel(observed, output_root),
        "loreview": rel(loreview, output_root),
        "repairplan": rel(repairplan, output_root),
        "source": "core_toy",
    }
    controlnet_entry = {
        "schema_version": "controlnet-sample-v1",
        "sample_id": sample_id,
        "control_image": rel(control_image, output_root),
        "control_mask": rel(control_mask, output_root),
        "target_image": rel(target_image, output_root),
        "correction_prompt": load_json(repairplan)["correction_prompt"],
        "prompt": load_json(repairplan)["correction_prompt"],
        "edit_type": "INSERT",
        "mask_type": "bbox",
        "repairplan_path": rel(repairplan, output_root),
        "repair_plan": rel(repairplan, output_root),
        "split": "toy",
    }
    planner_samples.append(planner_entry)
    controlnet_samples.append(controlnet_entry)
    samples.append(
        {
            "sample_id": sample_id,
            "source": "core_toy",
            "room_type": "bedroom",
            "architecture_json": rel(arch, output_root),
            "control_image": rel(control_image, output_root),
            "target_image": rel(target_image, output_root),
            "control_mask": rel(control_mask, output_root),
            "repairplan": rel(repairplan, output_root),
            "planner_sft_entry": True,
            "controlnet_repair_entry": True,
            "diffsynth_metadata_entry": True,
        }
    )


def add_semlayoutdiff(semlayoutdiff_root: Path, output_root: Path, dirs: dict[str, Path], samples: list[dict], warnings: list[str]) -> None:
    if not semlayoutdiff_root.exists():
        warnings.append("SemLayoutDiff toy output root missing; skipped.")
        return
    for arch_src in sorted((semlayoutdiff_root / "arch_json_v1").glob("*.json")):
        sample_id = arch_src.name.replace(".architecture_v1.json", "")
        arch = Path(copy_file(arch_src, dirs["arch_json"] / arch_src.name))
        condition_src = semlayoutdiff_root / "arch_condition_v1" / f"{sample_id}.arch_condition.png"
        semantic_src = semlayoutdiff_root / "gt_semantic_layout_v1" / f"{sample_id}.semantic_layout.png"
        condition = copy_file(condition_src, dirs["arch_condition"] / condition_src.name) if condition_src.exists() else None
        semantic = copy_file(semantic_src, dirs["gt_semantic"] / semantic_src.name) if semantic_src.exists() else None
        samples.append(
            {
                "sample_id": sample_id,
                "source": "semlayoutdiff_toy",
                "room_type": load_json(arch).get("room_type", "room"),
                "architecture_json": rel(arch, output_root),
                "architecture_condition": rel(Path(condition), output_root) if condition else None,
                "gt_semantic_layout": rel(Path(semantic), output_root) if semantic else None,
                "planner_sft_entry": False,
                "controlnet_repair_entry": False,
                "diffsynth_metadata_entry": False,
            }
        )


def add_editroom(editroom_root: Path, output_root: Path, dirs: dict[str, Path], samples: list[dict], planner_samples: list[dict], controlnet_samples: list[dict], warnings: list[str]) -> None:
    manifest_path = editroom_root / "controlnet_repair_v1" / "train.json"
    planner_manifest_path = editroom_root / "planner_sft_v1" / "planner_sft_manifest.json"
    if not manifest_path.exists() or not planner_manifest_path.exists():
        warnings.append("EditRoom toy manifests missing; skipped.")
        return
    edit_planner = {row["sample_id"]: row for row in load_json(planner_manifest_path).get("samples", [])}
    for row in load_json(manifest_path).get("samples", []):
        sample_id = row["sample_id"]
        control_image = Path(copy_file(editroom_root / row["control_image"], dirs["images"] / f"{sample_id}_control.png"))
        target_image = Path(copy_file(editroom_root / row["target_image"], dirs["targets"] / f"{sample_id}_target.png"))
        control_mask = Path(copy_file(editroom_root / row["control_mask"], dirs["masks"] / f"{sample_id}_control_mask.png"))
        repairplan = Path(copy_file(editroom_root / row["repairplan_path"], dirs["repairplans"] / f"{sample_id}_repairplan.json"))
        mask_spec_src = editroom_root / "masks" / "specs" / f"{sample_id}_mask_spec.json"
        if mask_spec_src.exists():
            copy_file(mask_spec_src, dirs["mask_specs"] / mask_spec_src.name)
        planner_row = edit_planner.get(sample_id)
        if planner_row:
            goal = Path(copy_file(editroom_root / "planner_sft_v1" / planner_row["goal_lostate"], dirs["goal"] / f"{sample_id}_goal_lostate.json"))
            observed = Path(copy_file(editroom_root / "planner_sft_v1" / planner_row["observed_lostate"], dirs["observed"] / f"{sample_id}_observed_lostate.json"))
            loreview = Path(copy_file(editroom_root / "planner_sft_v1" / planner_row["loreview"], dirs["loreview"] / f"{sample_id}_loreview.json"))
            planner_samples.append(
                {
                    "sample_id": sample_id,
                    "image": rel(control_image, output_root),
                    "instruction": planner_row.get("instruction", ""),
                    "goal_lostate": rel(goal, output_root),
                    "observed_lostate": rel(observed, output_root),
                    "loreview": rel(loreview, output_root),
                    "repairplan": rel(repairplan, output_root),
                    "source": "editroom_toy",
                    "edit_type": row.get("edit_type"),
                }
            )
        controlnet_entry = {
            "schema_version": "controlnet-sample-v1",
            "sample_id": sample_id,
            "control_image": rel(control_image, output_root),
            "control_mask": rel(control_mask, output_root),
            "target_image": rel(target_image, output_root),
            "correction_prompt": row.get("correction_prompt") or row.get("prompt"),
            "prompt": row.get("prompt") or row.get("correction_prompt"),
            "edit_type": row.get("edit_type", "INSERT"),
            "mask_type": row.get("mask_type", "bbox"),
            "repairplan_path": rel(repairplan, output_root),
            "repair_plan": rel(repairplan, output_root),
            "split": row.get("split", "train"),
        }
        controlnet_samples.append(controlnet_entry)
        samples.append(
            {
                "sample_id": sample_id,
                "source": "editroom_toy",
                "room_type": load_json(repairplan).get("source", {}).get("room_type", "bedroom"),
                "architecture_json": None,
                "control_image": rel(control_image, output_root),
                "target_image": rel(target_image, output_root),
                "control_mask": rel(control_mask, output_root),
                "repairplan": rel(repairplan, output_root),
                "planner_sft_entry": bool(planner_row),
                "controlnet_repair_entry": True,
                "diffsynth_metadata_entry": True,
            }
        )


def write_diffsynth_package(controlnet_samples: list[dict], output_root: Path, dirs: dict[str, Path]) -> None:
    rows = []
    for sample in controlnet_samples:
        sid = sample["sample_id"]
        control_dst = Path(copy_file(output_root / sample["control_image"], dirs["diffsynth_images"] / f"{sid}_control.png"))
        target_dst = Path(copy_file(output_root / sample["target_image"], dirs["diffsynth_targets"] / f"{sid}_target.png"))
        mask_dst = Path(copy_file(output_root / sample["control_mask"], dirs["diffsynth_masks"] / f"{sid}_mask.png"))
        rows.append(
            {
                "image": rel(target_dst, output_root),
                "blockwise_controlnet_image": rel(control_dst, output_root),
                "blockwise_controlnet_inpaint_mask": rel(mask_dst, output_root),
                "prompt": sample["prompt"],
            }
        )
    with (dirs["diffsynth"] / "metadata.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "blockwise_controlnet_image", "blockwise_controlnet_inpaint_mask", "prompt"])
        writer.writeheader()
        writer.writerows(rows)


def build_package(toy_root: Path, semlayoutdiff_root: Path, editroom_root: Path, output_root: Path) -> dict:
    dirs = ensure_dirs(output_root)
    samples: list[dict] = []
    planner_samples: list[dict] = []
    controlnet_samples: list[dict] = []
    warnings: list[str] = []

    add_core_toy(toy_root, output_root, dirs, samples, planner_samples, controlnet_samples, warnings)
    add_semlayoutdiff(semlayoutdiff_root, output_root, dirs, samples, warnings)
    add_editroom(editroom_root, output_root, dirs, samples, planner_samples, controlnet_samples, warnings)

    write_json(dirs["planner"] / "planner_sft_manifest.json", {"schema_version": "planner-sft-manifest-v1", "samples": planner_samples})
    write_json(dirs["planner"] / "qwenvl_sft.json", convert_qwenvl_rows(planner_samples, output_root))
    write_json(dirs["controlnet"] / "train.json", {"schema_version": "controlnet-repair-manifest-v1", "samples": controlnet_samples})
    write_diffsynth_package(controlnet_samples, output_root, dirs)

    artifact_counts = {
        "samples": len(samples),
        "planner_sft_entries": len(planner_samples),
        "controlnet_repair_entries": len(controlnet_samples),
        "diffsynth_metadata_entries": len(controlnet_samples),
        "architecture_json": len(list(dirs["arch_json"].glob("*.json"))),
        "repairplans": len(list(dirs["repairplans"].glob("*.json"))),
        "masks": len(list(dirs["masks"].glob("*.png"))),
    }
    package_manifest = {
        "schema_version": "unified-toy-package-v1",
        "package_version": "unified_toy_package_v1",
        "interface_tag": INTERFACE_TAG,
        "source_tags": SOURCE_TAGS,
        "samples": samples,
        "artifact_counts": artifact_counts,
        "created_from": {
            "toy_root": toy_root.as_posix(),
            "semlayoutdiff_root": semlayoutdiff_root.as_posix(),
            "editroom_root": editroom_root.as_posix(),
        },
        "notes": [
            "Toy-level package only; no real 3D-FRONT/3D-FUTURE, model weights, or training outputs are included.",
            "All package manifest paths are relative to the package root.",
        ],
    }
    write_json(output_root / "package_manifest.json", package_manifest)
    report = {
        "schema_version": "unified-package-report-v1",
        "package_root": output_root.as_posix(),
        "artifact_counts": artifact_counts,
        "warnings": warnings,
    }
    write_json(dirs["reports"] / "unified_package_report.json", report)
    return package_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toy-root", type=Path, default=Path("examples/toy_samples"), help="Base toy samples root.")
    parser.add_argument("--semlayoutdiff-root", type=Path, default=Path("outputs/semlayoutdiff_toy_loreflection"), help="SemLayoutDiff toy output root.")
    parser.add_argument("--editroom-root", type=Path, default=Path("outputs/editroom_toy_loreflection"), help="EditRoom toy output root.")
    parser.add_argument("--output-root", type=Path, default=Path("outputs/unified_toy_package_v1"), help="Unified package output root.")
    parser.add_argument("--mode", choices=["toy"], default="toy", help="Build mode.")
    args = parser.parse_args()

    build_package(args.toy_root, args.semlayoutdiff_root, args.editroom_root, args.output_root)
    print(f"Wrote unified toy package to {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
