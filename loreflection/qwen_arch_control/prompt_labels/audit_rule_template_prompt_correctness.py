from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


GEOMETRY = re.compile(r"\b(center_m|size_m|orientation_deg|bbox|footprint|metric_transform|source_json_path|px|pixel|meter|cm|coordinate)\b", re.I)
APPEARANCE = re.compile(r"\b(specific color palette|correct color palette|beautiful|modern|cozy|wood|fabric|material|texture|style|realistic|rgb|color)\b", re.I)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_counts(goal: dict[str, Any]) -> dict[str, int]:
    if isinstance(goal.get("required_counts"), dict):
        return {str(k): int(v) for k, v in goal["required_counts"].items()}
    counts: dict[str, int] = {}
    for slot in goal.get("furniture_slots", []):
        if not isinstance(slot, dict):
            continue
        category = slot.get("category") or slot.get("semantic_category")
        count = int(slot.get("count") or slot.get("required_count") or 1)
        if category:
            counts[str(category)] = counts.get(str(category), 0) + count
    return counts


def audit_rule_template_prompt_correctness(metadata_path: str | Path, dataset_base: str | Path) -> dict[str, Any]:
    metadata = Path(metadata_path)
    base = Path(dataset_base)
    rows = list(csv.DictReader(metadata.open(encoding="utf-8"))) if metadata.exists() else []
    failures: list[dict[str, Any]] = []
    checked = 0
    for row in rows:
        checked += 1
        prompt = row.get("prompt", "")
        prompt_l = prompt.lower()
        goal_path = base / row.get("goal_lostate", "")
        required = {}
        if goal_path.exists():
            required = _required_counts(_read_json(goal_path))
        for category, count in required.items():
            if category.lower().replace("_", " ") not in prompt_l and category.lower() not in prompt_l:
                failures.append({"sample_id": row.get("sample_id"), "metadata_source": metadata.as_posix(), "issue_type": "missing_required_category", "expected": category, "observed": prompt})
            if str(count) not in prompt_l and count > 1:
                failures.append({"sample_id": row.get("sample_id"), "metadata_source": metadata.as_posix(), "issue_type": "missing_required_count", "expected": {category: count}, "observed": prompt})
        if GEOMETRY.search(prompt):
            failures.append({"sample_id": row.get("sample_id"), "metadata_source": metadata.as_posix(), "issue_type": "geometry_leakage", "expected": "no geometry words", "observed": prompt})
        if APPEARANCE.search(prompt):
            failures.append({"sample_id": row.get("sample_id"), "metadata_source": metadata.as_posix(), "issue_type": "appearance_style_color_wording_risk", "expected": "no appearance/style/color wording", "observed": prompt})
        if "architecture condition image" not in prompt_l and not ("architecture" in prompt_l and "condition" in prompt_l):
            failures.append({"sample_id": row.get("sample_id"), "metadata_source": metadata.as_posix(), "issue_type": "missing_architecture_condition_reference", "expected": "architecture condition image", "observed": prompt})
        if "Palette_Control." not in prompt and "frozen semantic palette" not in prompt_l:
            failures.append({"sample_id": row.get("sample_id"), "metadata_source": metadata.as_posix(), "issue_type": "missing_palette_control", "expected": "Palette_Control or frozen semantic palette", "observed": prompt})
    return {
        "metadata_path": metadata.as_posix(),
        "dataset_base": base.as_posix(),
        "num_rows": len(rows),
        "checked_rows": checked,
        "failure_count": len(failures),
        "status": "pass" if rows and not failures else "fail" if rows else "not_verified",
        "failure_examples": failures[:100],
    }
