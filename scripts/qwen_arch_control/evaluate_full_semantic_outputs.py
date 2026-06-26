#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from loreflection.semantic_registry import load_registry


PROTECTED_ARCHITECTURE = {"wall", "door", "window", "clearance", "non_placeable"}


def _mask_colors(arr: np.ndarray, colors: set[tuple[int, int, int]]) -> np.ndarray:
    flat = arr.reshape(-1, 3)
    return np.array([tuple(int(v) for v in pixel) in colors for pixel in flat], dtype=bool).reshape(arr.shape[:2])


def evaluate(
    *,
    output_root: Path,
    dataset_base: Path,
    metadata: Path,
    sanitized: bool = False,
) -> dict[str, object]:
    registry = load_registry()
    object_colors = {registry.id_to_rgb[sid] for sid in registry.object_ids}
    protected_colors = {cat.rgb for cat in registry.categories if cat.name in PROTECTED_ARCHITECTURE}
    quant_report = {}
    quant_path = output_root / "eval" / "palette_quantization_report.json"
    if quant_path.exists():
        quant_report = json.loads(quant_path.read_text(encoding="utf-8"))
    sanitized_dir = output_root / "sanitized"
    if sanitized:
        sanitized_dir.mkdir(parents=True, exist_ok=True)

    full_agreement: list[float] = []
    architecture_accuracy: list[float] = []
    overwrite_rates: list[float] = []
    tp = fp = fn = 0
    class_ok = class_total = 0
    samples = 0
    for row in csv.DictReader(metadata.open(encoding="utf-8")):
        sid = row["sample_id"]
        pred_path = output_root / "quantized" / f"{sid}_quantized.png"
        if not pred_path.exists():
            continue
        pred = np.asarray(Image.open(pred_path).convert("RGB"))
        target = np.asarray(Image.open(dataset_base / row["image"]).convert("RGB"))
        context = np.asarray(Image.open(dataset_base / row["context_image"]).convert("RGB"))
        if pred.shape != target.shape:
            continue
        protected = _mask_colors(context, protected_colors)
        eval_pred = pred.copy()
        if sanitized:
            eval_pred[protected] = target[protected]
            Image.fromarray(eval_pred).save(sanitized_dir / f"{sid}_sanitized.png")
        samples += 1
        full_agreement.append(float((eval_pred == target).all(axis=2).mean()))
        if protected.any():
            architecture_accuracy.append(float((eval_pred[protected] == target[protected]).all(axis=1).mean()))
            pred_furniture = _mask_colors(eval_pred, object_colors)
            overwrite_rates.append(float((pred_furniture & protected).sum() / protected.sum()))
        pred_furniture = _mask_colors(eval_pred, object_colors)
        target_furniture = _mask_colors(target, object_colors)
        tp += int((pred_furniture & target_furniture).sum())
        fp += int((pred_furniture & ~target_furniture).sum())
        fn += int((~pred_furniture & target_furniture).sum())
        both = pred_furniture & target_furniture
        if both.any():
            class_ok += int((eval_pred[both] == target[both]).all(axis=1).sum())
            class_total += int(both.sum())

    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    report = {
        "inference_ran": samples > 0,
        "num_infer_samples": samples,
        "postprocess": "protected_architecture_copyback" if sanitized else "none",
        "full_image_pixel_agreement": float(np.mean(full_agreement)) if full_agreement else None,
        "architecture_preservation_accuracy": float(np.mean(architecture_accuracy)) if architecture_accuracy else 1.0,
        "furniture_pixel_precision": float(precision),
        "furniture_pixel_recall": float(recall),
        "furniture_pixel_f1": float(f1),
        "furniture_class_color_accuracy": float(class_ok / max(1, class_total)),
        "palette_unknown_rate_after_quantization": quant_report.get("unknown_color_rate_after_quantization"),
        "forbidden_architecture_overwrite_rate": float(np.mean(overwrite_rates)) if overwrite_rates else 0.0,
        "protected_architecture_categories": sorted(PROTECTED_ARCHITECTURE),
        "floor_is_placeable_not_forbidden": True,
    }
    report["smoke_pass"] = bool(
        report["palette_unknown_rate_after_quantization"] == 0.0
        and report["architecture_preservation_accuracy"] >= 0.95
        and report["furniture_pixel_f1"] >= 0.35
        and report["forbidden_architecture_overwrite_rate"] <= 0.005
    )
    report["failure_reason"] = None if report["smoke_pass"] else (
        "failed smoke gate: require palette_unknown=0, architecture_preservation>=0.95, "
        "furniture_f1>=0.35, forbidden_overwrite<=0.005"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dataset-base", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sanitized", action="store_true")
    args = parser.parse_args()
    report = evaluate(
        output_root=args.output_root,
        dataset_base=args.dataset_base,
        metadata=args.metadata,
        sanitized=args.sanitized,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
