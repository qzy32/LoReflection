from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from loreflection.semantic_registry import load_registry


GEOMETRY = re.compile(r"\b(center_m|size_m|orientation_deg|bbox|footprint|metric_transform|source_json_path|px|pixel|meter|cm|coordinate)\b", re.I)
APPEARANCE = re.compile(r"\b(beautiful|modern|cozy|wood|fabric|material|texture|style|realistic|lighting|shadow|gradient|anti-aliasing|specific color palette|correct color palette)\b", re.I)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rate(n: int, d: int) -> float | None:
    return None if d == 0 else n / d


def _required_counts(goal: dict[str, Any]) -> dict[str, int]:
    if isinstance(goal.get("required_counts"), dict):
        return {str(k): int(v) for k, v in goal["required_counts"].items()}
    counts: dict[str, int] = {}
    for slot in goal.get("furniture_slots", []):
        if isinstance(slot, dict):
            category = slot.get("category") or slot.get("semantic_category")
            count = int(slot.get("count") or slot.get("required_count") or 1)
            if category:
                counts[str(category)] = counts.get(str(category), 0) + count
    return counts


def audit_metadata_palette_contract(
    metadata_path: str | Path,
    dataset_base: str | Path,
    prediction_dir: str | Path | None = None,
    quantized_dir: str | Path | None = None,
) -> dict[str, Any]:
    metadata = Path(metadata_path)
    base = Path(dataset_base)
    rows = list(csv.DictReader(metadata.open(encoding="utf-8"))) if metadata.exists() else []
    total = len(rows)
    counters = Counter()
    failures: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        prompt = row.get("prompt", "")
        if prompt.startswith("Context_Control."):
            counters["context"] += 1
        if "Palette_Control." in prompt:
            counters["palette_control"] += 1
        if "Architecture_Control." in prompt:
            counters["architecture_control"] += 1
        if GEOMETRY.search(prompt):
            counters["geometry_leak"] += 1
        if APPEARANCE.search(prompt):
            counters["appearance_word"] += 1
            failures.append({"row": idx, "sample_id": row.get("sample_id"), "issue_type": "appearance_or_color_wording", "prompt": prompt})
        pkg_path = base / row.get("prompt_package", "")
        goal_path = base / row.get("goal_lostate", "")
        if pkg_path.exists():
            pkg = _read_json(pkg_path)
            if pkg.get("palette_contract_ref"):
                counters["palette_contract_ref"] += 1
            active = pkg.get("active_palette_entries")
            if isinstance(active, dict) and active:
                counters["active_palette_entries"] += 1
            if goal_path.exists() and isinstance(active, dict):
                required = set(_required_counts(_read_json(goal_path)))
                if required.issubset(set(active)):
                    counters["active_covers_required"] += 1
        else:
            failures.append({"row": idx, "sample_id": row.get("sample_id"), "issue_type": "missing_prompt_package", "path": str(pkg_path)})
    report = {
        "metadata_path": metadata.as_posix(),
        "dataset_base": base.as_posix(),
        "num_rows": total,
        "palette_contract_ref_exists_rate": _rate(counters["palette_contract_ref"], total),
        "active_palette_entries_exists_rate": _rate(counters["active_palette_entries"], total),
        "active_palette_entries_cover_required_categories_rate": _rate(counters["active_covers_required"], total),
        "compiled_prompt_has_palette_control_rate": _rate(counters["palette_control"], total),
        "compiled_prompt_has_architecture_control_rate": _rate(counters["architecture_control"], total),
        "prompt_starts_with_context_control_rate": _rate(counters["context"], total),
        "coordinate_leakage_rate": _rate(counters["geometry_leak"], total),
        "appearance_word_rate": _rate(counters["appearance_word"], total),
        "forbidden_color_style_phrase_rate": _rate(counters["appearance_word"], total),
        "failure_examples": failures[:50],
    }
    report.update(class_color_confusion(metadata, base, quantized_dir))
    return report


def class_color_confusion(metadata_path: Path, dataset_base: Path, quantized_dir: str | Path | None = None) -> dict[str, Any]:
    if not quantized_dir:
        return {
            "prediction_class_color_confusion_status": "skipped",
            "reason": "Prediction class-color confusion audit skipped because prediction outputs are missing for this metadata source.",
        }
    qdir = Path(quantized_dir)
    if not qdir.exists():
        return {
            "prediction_class_color_confusion_status": "skipped",
            "reason": f"quantized_dir not found: {qdir}",
        }
    registry = load_registry()
    rgb_to_name = {tuple(cat.rgb): cat.name for cat in registry.categories}
    rows = list(csv.DictReader(metadata_path.open(encoding="utf-8"))) if metadata_path.exists() else []
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    total = 0
    correct = 0
    furniture_total = 0
    furniture_correct = 0
    object_names = {registry.id_to_name[sid] for sid in registry.object_ids}
    for row in rows:
        sid = row.get("sample_id", "")
        target_path = dataset_base / row.get("image", "")
        pred_path = qdir / f"{sid}_quantized.png"
        if not target_path.exists() or not pred_path.exists():
            continue
        target = np.asarray(Image.open(target_path).convert("RGB"))
        pred = np.asarray(Image.open(pred_path).convert("RGB").resize((target.shape[1], target.shape[0]), Image.Resampling.NEAREST))
        flat_t = target.reshape(-1, 3)
        flat_p = pred.reshape(-1, 3)
        for t_rgb, p_rgb in zip(flat_t, flat_p):
            t_name = rgb_to_name.get(tuple(int(v) for v in t_rgb), "unknown")
            p_name = rgb_to_name.get(tuple(int(v) for v in p_rgb), "unknown")
            matrix[t_name][p_name] += 1
            total += 1
            if t_name == p_name:
                correct += 1
            if t_name in object_names:
                furniture_total += 1
                if t_name == p_name:
                    furniture_correct += 1
    if total == 0:
        return {"prediction_class_color_confusion_status": "skipped", "reason": "no matching target/prediction pairs found"}
    most_confused = []
    for t_name, row in matrix.items():
        for p_name, count in row.items():
            if t_name != p_name:
                most_confused.append({"target_category": t_name, "pred_category": p_name, "pixels": count})
    most_confused.sort(key=lambda item: item["pixels"], reverse=True)
    return {
        "prediction_class_color_confusion_status": "computed",
        "class_color_pixel_accuracy": correct / total,
        "furniture_class_color_pixel_accuracy": None if furniture_total == 0 else furniture_correct / furniture_total,
        "most_confused_pairs": most_confused[:20],
        "confusion_matrix": {k: dict(v) for k, v in matrix.items()},
    }
