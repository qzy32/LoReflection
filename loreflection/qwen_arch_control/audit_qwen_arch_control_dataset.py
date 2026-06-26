"""Audit the complete Qwen Architecture In-Context P0 package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from PIL import Image
from jsonschema import Draft202012Validator

from loreflection.semantic_registry import load_registry
from tools.audit_prompt_geometry_leakage import find_leaks


PATH_COLUMNS = ["image", "context_image", "goal_lostate", "prompt_package", "verifier_refs"]
ROOT = Path(__file__).resolve().parents[2]
GOAL_SCHEMA_PATH = ROOT / "artifacts" / "current_interface" / "goal_lostate.schema.json"


def _rate(values: list[bool]) -> float:
    return sum(values) / max(1, len(values))


def _image_colors(path: Path) -> set[tuple[int, int, int]]:
    image = Image.open(path).convert("RGB")
    return {rgb for _, rgb in image.getcolors(maxcolors=image.width * image.height) or []}


def audit_dataset(dataset_root: Path) -> dict[str, Any]:
    registry = load_registry()
    package_manifest_path = dataset_root / "meta" / "p0_dataset_manifest.json"
    package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    source_mode = str(package_manifest.get("source_mode", "unknown"))
    goal_validator = Draft202012Validator(json.loads(GOAL_SCHEMA_PATH.read_text(encoding="utf-8")))
    furniture_colors = {
        category.rgb for category in registry.categories if category.semantic_id in registry.object_ids
    }
    rows = []
    with (dataset_root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    path_exists = []
    image_exists = []
    context_exists = []
    ids_match = []
    same_resolution = []
    condition_clean = []
    target_has_furniture = []
    prompt_prefix = []
    prompt_clean = []
    slot_coverage = []
    layout_exists = []
    goal_valid = []
    target_from_layout = []
    condition_from_architecture = []
    real_source = []
    procedural_source = []
    sample_reports = []

    for row in rows:
        resolved = {column: dataset_root / row[column] for column in PATH_COLUMNS}
        exists = {column: path.exists() for column, path in resolved.items()}
        path_exists.append(all(exists.values()))
        image_exists.append(exists["image"])
        context_exists.append(exists["context_image"])
        prompt_prefix.append(row["prompt"].startswith("Context_Control."))
        prompt_clean.append(not find_leaks(row["prompt"]))

        sample_id = row["sample_id"]
        sample_manifest_path = dataset_root / "meta" / f"{sample_id}_sample_manifest.json"
        sample_manifest = (
            json.loads(sample_manifest_path.read_text(encoding="utf-8"))
            if sample_manifest_path.exists()
            else {}
        )
        layout_path = dataset_root / "meta" / f"{sample_id}_layout.json"
        architecture_path = dataset_root / "meta" / f"{sample_id}_architecture.json"
        layout_exists.append(layout_path.exists())
        source_kind = str(sample_manifest.get("source_kind", ""))
        is_real = source_kind in {"raw_3dfront", "real_scene_package"}
        real_source.append(is_real)
        procedural_source.append(source_kind == "procedural_contract")
        target_from_layout.append(
            layout_path.exists()
            and sample_manifest.get("target_contract", {}).get("furniture_only") is True
        )
        condition_from_architecture.append(
            architecture_path.exists()
            and sample_manifest.get("condition_contract", {}).get("architecture_only") is True
        )
        ids_match.append(
            Path(row["image"]).name.startswith(sample_id)
            and Path(row["context_image"]).name.startswith(sample_id)
            and all(Path(row[column]).name.startswith(sample_id) for column in ("goal_lostate", "prompt_package", "verifier_refs"))
        )

        if exists["image"] and exists["context_image"]:
            target = Image.open(resolved["image"]).convert("RGB")
            condition = Image.open(resolved["context_image"]).convert("RGB")
            same_resolution.append(target.size == condition.size)
            target_colors = _image_colors(resolved["image"])
            condition_colors = _image_colors(resolved["context_image"])
            condition_clean.append(not (condition_colors & furniture_colors))
            target_has_furniture.append(bool(target_colors & furniture_colors))
        else:
            same_resolution.append(False)
            condition_clean.append(False)
            target_has_furniture.append(False)

        required_categories = []
        if exists["goal_lostate"]:
            goal = json.loads(resolved["goal_lostate"].read_text(encoding="utf-8"))
            goal_valid.append(not list(goal_validator.iter_errors(goal)))
            required_categories = [
                slot["category"] for slot in goal.get("furniture_slots", []) if slot.get("required", False)
            ]
        else:
            goal_valid.append(False)
        covered = all(category.replace("_", " ") in row["prompt"].replace("_", " ") for category in required_categories)
        slot_coverage.append(covered)
        sample_reports.append(
            {
                "sample_id": sample_id,
                "paths_exist": exists,
                "same_resolution": same_resolution[-1],
                "condition_contains_furniture": not condition_clean[-1],
                "target_has_furniture_pixels": target_has_furniture[-1],
                "prompt_leaks": find_leaks(row["prompt"]),
                "required_slots_covered": covered,
                "source_kind": source_kind,
                "layout_json_exists": layout_exists[-1],
                "goal_lostate_schema_valid": goal_valid[-1],
                "target_rendered_from_layout": target_from_layout[-1],
                "condition_rendered_from_architecture": condition_from_architecture[-1],
            }
        )

    split_path = dataset_root / "audits" / "split_report.json"
    split_report = json.loads(split_path.read_text(encoding="utf-8")) if split_path.exists() else {}
    report = {
        "num_samples": len(rows),
        "source_mode": source_mode,
        "real_source_rate": _rate(real_source),
        "procedural_source_rate": _rate(procedural_source),
        "layout_json_exists_rate": _rate(layout_exists),
        "goal_lostate_schema_valid_rate": _rate(goal_valid),
        "target_rendered_from_layout_rate": _rate(target_from_layout),
        "condition_rendered_from_architecture_rate": _rate(condition_from_architecture),
        "metadata_path_exists_rate": _rate(path_exists),
        "image_exists_rate": _rate(image_exists),
        "context_image_exists_rate": _rate(context_exists),
        "same_sample_id_consistency_rate": _rate(ids_match),
        "same_resolution_rate": _rate(same_resolution),
        "condition_contains_furniture_rate": 1.0 - _rate(condition_clean),
        "target_has_furniture_pixels_rate": _rate(target_has_furniture),
        "prompt_starts_with_context_control_rate": _rate(prompt_prefix),
        "prompt_coordinate_leakage_rate": 1.0 - _rate(prompt_clean),
        "required_slot_prompt_coverage_rate": _rate(slot_coverage),
        "train_val_test_scene_leakage_rate": float(split_report.get("train_val_test_scene_leakage_rate", 1.0)),
        "sample_reports": sample_reports,
    }
    expected = {
        "metadata_path_exists_rate": 1.0,
        "image_exists_rate": 1.0,
        "context_image_exists_rate": 1.0,
        "same_sample_id_consistency_rate": 1.0,
        "same_resolution_rate": 1.0,
        "condition_contains_furniture_rate": 0.0,
        "target_has_furniture_pixels_rate": 1.0,
        "prompt_starts_with_context_control_rate": 1.0,
        "prompt_coordinate_leakage_rate": 0.0,
        "required_slot_prompt_coverage_rate": 1.0,
        "train_val_test_scene_leakage_rate": 0.0,
        "layout_json_exists_rate": 1.0,
        "goal_lostate_schema_valid_rate": 1.0,
        "target_rendered_from_layout_rate": 1.0,
        "condition_rendered_from_architecture_rate": 1.0,
    }
    common_pass = len(rows) and all(report[key] == value for key, value in expected.items())
    if source_mode == "procedural_contract":
        report["training_ready"] = False
        report["status"] = (
            "contract_pass"
            if common_pass
            and report["real_source_rate"] == 0.0
            and report["procedural_source_rate"] == 1.0
            else "fail"
        )
    else:
        report["training_ready"] = bool(
            common_pass
            and report["real_source_rate"] == 1.0
            and report["procedural_source_rate"] == 0.0
        )
        report["status"] = "pass" if report["training_ready"] else "fail"
    output = dataset_root / "audits" / "dataset_audit_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    args = parser.parse_args()
    report = audit_dataset(args.dataset_root)
    print(json.dumps({key: value for key, value in report.items() if key != "sample_reports"}, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"pass", "contract_pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
