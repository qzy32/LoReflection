"""Audit the complete Qwen Architecture In-Context P0 package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from PIL import Image

from loreflection.semantic_registry import load_registry
from tools.audit_prompt_geometry_leakage import find_leaks


PATH_COLUMNS = ["image", "context_image", "goal_lostate", "prompt_package", "verifier_refs"]


def _rate(values: list[bool]) -> float:
    return sum(values) / max(1, len(values))


def _image_colors(path: Path) -> set[tuple[int, int, int]]:
    image = Image.open(path).convert("RGB")
    return {rgb for _, rgb in image.getcolors(maxcolors=image.width * image.height) or []}


def audit_dataset(dataset_root: Path) -> dict[str, Any]:
    registry = load_registry()
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
            required_categories = [
                slot["category"] for slot in goal.get("furniture_slots", []) if slot.get("required", False)
            ]
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
            }
        )

    split_path = dataset_root / "audits" / "split_report.json"
    split_report = json.loads(split_path.read_text(encoding="utf-8")) if split_path.exists() else {}
    report = {
        "num_samples": len(rows),
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
    }
    report["status"] = "pass" if len(rows) and all(report[key] == value for key, value in expected.items()) else "fail"
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
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
