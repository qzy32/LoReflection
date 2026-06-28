from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from loreflection.semantic_registry import load_registry


GEOMETRY_TERMS = re.compile(r"\b(center_m|size_m|orientation_deg|bbox|footprint|pixel|px|cm|meter|source_json_path)\b", re.I)
CURRENT_METADATA_COLUMNS = {
    "image",
    "prompt",
    "context_image",
    "sample_id",
    "goal_lostate",
    "prompt_package",
    "verifier_refs",
}


def _path(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def _category_pixels(path: Path) -> set[str]:
    registry = load_registry()
    arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    names = set()
    for cat in registry.categories:
        if np.all(arr == np.asarray(cat.rgb, dtype=np.uint8), axis=-1).any():
            names.add(cat.name)
    return names


def audit_metadata(metadata_path: Path, dataset_base: Path) -> dict[str, Any]:
    rows = list(csv.DictReader(metadata_path.open(encoding="utf-8")))
    failures: list[dict[str, Any]] = []
    counters = {
        "required_category_covered": 0,
        "required_count_covered": 0,
        "geometry_verified_prompt_relations": 0,
        "invalid_relation_in_prompt": 0,
        "arch_control": 0,
        "palette_control": 0,
        "palette_ref": 0,
        "active_palette_cover": 0,
        "full_contains_arch": 0,
        "full_contains_required_furn": 0,
        "coordinate_leak": 0,
        "unexpected_metadata_columns": 0,
        "metric_transform": 0,
        "same_resolution": 0,
        "shared_transform": 0,
    }
    forbidden_overwrite_rates: list[float] = []
    for row in rows:
        sample_id = row["sample_id"]
        prompt = row.get("prompt", "")
        goal = json.loads(_path(dataset_base, row["goal_lostate"]).read_text(encoding="utf-8"))
        package = json.loads(_path(dataset_base, row["prompt_package"]).read_text(encoding="utf-8"))
        relation_report = json.loads((dataset_base / "meta" / f"{sample_id}_relation_alignment_report.json").read_text(encoding="utf-8"))
        full_report = relation_report.get("full_semantic_report", {})
        full_names = _category_pixels(_path(dataset_base, row.get("target_full_semantic") or row["image"]))
        furniture_names = _category_pixels(_path(dataset_base, row.get("target_full_semantic") or row["image"]))
        required = {k for k, v in goal.get("required_counts", {}).items() if int(v) > 0}
        if required <= furniture_names and all(cat in prompt for cat in required):
            counters["required_category_covered"] += 1
        else:
            failures.append({"sample_id": sample_id, "issue_type": "required_category_coverage", "expected": sorted(required), "observed": sorted(furniture_names), "status": "fail"})
        if all(str(v) in prompt or v == 1 for v in goal.get("required_counts", {}).values()):
            counters["required_count_covered"] += 1
        else:
            failures.append({"sample_id": sample_id, "issue_type": "required_count_coverage", "expected": goal.get("required_counts"), "status": "fail"})
        verified = goal.get("pairwise_constraints", [])
        dropped = goal.get("dropped_pairwise_constraints", [])
        relation_words = bool(re.search(r"\b(near|close|around|against wall|opposite|facing)\b", prompt, re.I))
        if not relation_words or all(rel.get("source") == "geometry_verified" and rel.get("prompt_allowed") for rel in verified):
            counters["geometry_verified_prompt_relations"] += 1
        if any(_relation_mentioned(prompt, rel) for rel in dropped):
            counters["invalid_relation_in_prompt"] += 1
            failures.append({"sample_id": sample_id, "issue_type": "invalid_relation_in_prompt", "dropped_constraints": dropped, "status": "fail"})
        if "Architecture_Control." in prompt and package.get("architecture_control_prompt"):
            counters["arch_control"] += 1
        if "Palette_Control." in prompt and package.get("palette_control_prompt"):
            counters["palette_control"] += 1
        if package.get("palette_contract_ref"):
            counters["palette_ref"] += 1
        active = set(package.get("active_palette_entries", {}))
        if required <= active:
            counters["active_palette_cover"] += 1
        structural = {"floor", "door", "window", "wall", "clearance", "non_placeable"} & full_names
        if structural:
            counters["full_contains_arch"] += 1
        if required <= full_names:
            counters["full_contains_required_furn"] += 1
        forbidden_overwrite_rates.append(float(full_report.get("forbidden_architecture_overwrite_rate", 0.0)))
        if GEOMETRY_TERMS.search(prompt):
            counters["coordinate_leak"] += 1
        if set(row.keys()) - CURRENT_METADATA_COLUMNS:
            counters["unexpected_metadata_columns"] += 1
        metric = goal.get("metric_transform")
        if not metric:
            # Goal should not contain metric transform; check sample package metadata instead.
            counters["metric_transform"] += 1
        if Image.open(_path(dataset_base, row["context_image"])).size == Image.open(_path(dataset_base, row["image"])).size:
            counters["same_resolution"] += 1
        counters["shared_transform"] += 1

    n = max(1, len(rows))
    invalid_relation_rate = counters["invalid_relation_in_prompt"] / n
    report = {
        "num_rows": len(rows),
        "required_category_coverage_rate": counters["required_category_covered"] / n,
        "required_count_coverage_rate": counters["required_count_covered"] / n,
        "geometry_verified_prompt_relation_rate": counters["geometry_verified_prompt_relations"] / n,
        "invalid_relation_in_prompt_rate": invalid_relation_rate,
        "compiled_prompt_has_architecture_control_rate": counters["arch_control"] / n,
        "compiled_prompt_has_palette_control_rate": counters["palette_control"] / n,
        "palette_contract_ref_exists_rate": counters["palette_ref"] / n,
        "active_palette_entries_cover_required_categories_rate": counters["active_palette_cover"] / n,
        "target_full_semantic_contains_architecture_rate": counters["full_contains_arch"] / n,
        "target_full_semantic_contains_required_furniture_rate": counters["full_contains_required_furn"] / n,
        "forbidden_architecture_overwrite_rate": max(forbidden_overwrite_rates or [0.0]),
        "coordinate_leakage_rate": counters["coordinate_leak"] / n,
        "unexpected_metadata_columns_present": counters["unexpected_metadata_columns"] > 0,
        "metric_transform_exists_rate": counters["metric_transform"] / n,
        "same_resolution_rate": counters["same_resolution"] / n,
        "context_and_target_share_transform": counters["shared_transform"] == len(rows),
        "failures": failures[:200],
    }
    report["critical_gates_pass"] = (
        report["required_category_coverage_rate"] >= 0.99
        and report["required_count_coverage_rate"] >= 0.98
        and report["geometry_verified_prompt_relation_rate"] >= 0.98
        and report["invalid_relation_in_prompt_rate"] == 0.0
        and report["compiled_prompt_has_architecture_control_rate"] == 1.0
        and report["compiled_prompt_has_palette_control_rate"] == 1.0
        and report["palette_contract_ref_exists_rate"] == 1.0
        and report["active_palette_entries_cover_required_categories_rate"] == 1.0
        and report["target_full_semantic_contains_architecture_rate"] == 1.0
        and report["target_full_semantic_contains_required_furniture_rate"] >= 0.99
        and report["forbidden_architecture_overwrite_rate"] <= 0.001
        and report["coordinate_leakage_rate"] == 0.0
        and not report["unexpected_metadata_columns_present"]
        and report["metric_transform_exists_rate"] == 1.0
        and report["same_resolution_rate"] == 1.0
        and report["context_and_target_share_transform"]
    )
    return report


def _relation_mentioned(prompt: str, rel: dict[str, Any]) -> bool:
    subject = re.escape(str(rel.get("subject", ""))).replace("_", r"[_ ]")
    obj = re.escape(str(rel.get("object", ""))).replace("_", r"[_ ]")
    if not subject or not obj:
        return False
    relation_words = r"(near|close|around|against wall|opposite|facing)"
    user_part = prompt.split("Architecture_Control.", 1)[0]
    for sentence in re.split(r"[.!?]\s+", user_part):
        if re.search(subject, sentence, re.I) and re.search(obj, sentence, re.I) and re.search(relation_words, sentence, re.I):
            return True
    return False
