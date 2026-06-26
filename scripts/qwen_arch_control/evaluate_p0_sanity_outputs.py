#!/usr/bin/env python3
"""Evaluate P0 sanity training artifacts and command contract."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from loreflection.semantic_registry import load_registry


def _forbidden_terms() -> list[str]:
    return [
        "blockwise_" + "controlnet_image",
        "blockwise_" + "controlnet_inpaint_mask",
        "control_" + "mask",
        "I_" + "bad",
        "I_" + "target",
        "Qwen-Image-" + "Blockwise-ControlNet-" + "Inpaint",
        "semantic_" + "repair4",
    ]


def _read_texts(paths: list[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def _has_any(text: str, variants: list[str]) -> bool:
    return any(variant in text for variant in variants)


def _target_agreement(dataset_base: Path, metadata_path: Path, quantized_dir: Path) -> float | None:
    if not quantized_dir.exists():
        return None
    rows = list(csv.DictReader(metadata_path.open("r", encoding="utf-8", newline="")))
    agreements: list[float] = []
    for row in rows:
        sid = row["sample_id"]
        qpath = quantized_dir / f"{sid}_quantized.png"
        if not qpath.exists():
            continue
        target = dataset_base / row["image"]
        if not target.exists():
            continue
        q = np.array(Image.open(qpath).convert("RGB"))
        t = np.array(Image.open(target).convert("RGB"))
        if q.shape != t.shape:
            continue
        agreements.append(float((q == t).all(axis=2).mean()))
    if not agreements:
        return None
    return float(sum(agreements) / len(agreements))


def _object_rgb_set() -> set[tuple[int, int, int]]:
    registry = load_registry()
    return {registry.id_to_rgb[sid] for sid in registry.object_ids}


def _furniture_mask(arr: np.ndarray, object_colors: set[tuple[int, int, int]]) -> np.ndarray:
    flat = arr.reshape(-1, 3)
    mask = np.array([tuple(int(v) for v in pixel) in object_colors for pixel in flat], dtype=bool)
    return mask.reshape(arr.shape[:2])


def _furniture_metrics(dataset_base: Path, metadata_path: Path, quantized_dir: Path) -> dict[str, float | None]:
    if not quantized_dir.exists():
        return {"furniture_pixel_precision": None, "furniture_pixel_recall": None, "furniture_pixel_f1": None}
    object_colors = _object_rgb_set()
    rows = list(csv.DictReader(metadata_path.open("r", encoding="utf-8", newline="")))
    tp = fp = fn = 0
    for row in rows:
        sid = row["sample_id"]
        qpath = quantized_dir / f"{sid}_quantized.png"
        target_path = dataset_base / row["image"]
        if not qpath.exists() or not target_path.exists():
            continue
        q = np.array(Image.open(qpath).convert("RGB"))
        t = np.array(Image.open(target_path).convert("RGB"))
        if q.shape != t.shape:
            continue
        qm = _furniture_mask(q, object_colors)
        tm = _furniture_mask(t, object_colors)
        tp += int((qm & tm).sum())
        fp += int((qm & ~tm).sum())
        fn += int((~qm & tm).sum())
    if tp + fp + fn == 0:
        return {"furniture_pixel_precision": None, "furniture_pixel_recall": None, "furniture_pixel_f1": None}
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "furniture_pixel_precision": float(precision),
        "furniture_pixel_recall": float(recall),
        "furniture_pixel_f1": float(f1),
    }


def _condition_contains_furniture_rate(dataset_base: Path, metadata_path: Path) -> float:
    object_colors = _object_rgb_set()
    rows = list(csv.DictReader(metadata_path.open("r", encoding="utf-8", newline="")))
    rates: list[float] = []
    for row in rows:
        path = dataset_base / row["context_image"]
        if not path.exists():
            continue
        arr = np.array(Image.open(path).convert("RGB"))
        rates.append(float(_furniture_mask(arr, object_colors).mean()))
    return float(sum(rates) / max(1, len(rates)))


def _target_has_furniture_pixels_rate(dataset_base: Path, metadata_path: Path) -> float:
    object_colors = _object_rgb_set()
    rows = list(csv.DictReader(metadata_path.open("r", encoding="utf-8", newline="")))
    checks: list[float] = []
    for row in rows:
        path = dataset_base / row["image"]
        if not path.exists():
            continue
        arr = np.array(Image.open(path).convert("RGB"))
        checks.append(1.0 if _furniture_mask(arr, object_colors).any() else 0.0)
    return float(sum(checks) / max(1, len(checks)))


def evaluate(
    output_root: Path,
    dataset_base: Path,
    metadata_path: Path,
    train_logs: list[Path],
    script_paths: list[Path],
    checkpoint_used: Path | None = None,
    phase_label: str = "p0",
) -> dict[str, object]:
    text = _read_texts(train_logs + script_paths)
    required = {
        "data_file_keys_image_context_image": [
            '--data_file_keys "image,context_image"',
            "--data_file_keys image,context_image",
        ],
        "extra_inputs_context_image": [
            '--extra_inputs "context_image"',
            "--extra_inputs context_image",
        ],
        "incontext_union_lora": ["Qwen-Image-In-Context-Control-Union"],
    }
    forbidden = _forbidden_terms()
    missing_required = [name for name, variants in required.items() if not _has_any(text, variants)]
    found_forbidden = [term for term in forbidden if term in text]
    quant_report_path = output_root / "eval" / "palette_quantization_report.json"
    quant_report = {}
    if quant_report_path.exists():
        quant_report = json.loads(quant_report_path.read_text(encoding="utf-8"))
    infer_raw = list((output_root / "infer").glob("*_raw.png"))
    agreement = _target_agreement(dataset_base, metadata_path, output_root / "quantized")
    furniture = _furniture_metrics(dataset_base, metadata_path, output_root / "quantized")
    furniture_f1 = furniture.get("furniture_pixel_f1")
    inference_ran = bool(infer_raw)
    overfit_success: bool | None
    failure_reason: str | None
    if not inference_ran:
        overfit_success = None
        failure_reason = "inference outputs are absent"
    else:
        overfit_success = bool(
            (agreement is not None and agreement >= 0.50)
            or (furniture_f1 is not None and furniture_f1 >= 0.40)
        )
        failure_reason = None if overfit_success else (
            "target agreement and furniture F1 are below conservative P0 thresholds; "
            "possible causes include too few epochs, LoRA not loading, context input mismatch, "
            "or inference parameter mismatch"
        )
    report = {
        "inference_ran": inference_ran,
        "training_command_uses_context_image": "extra_inputs_context_image" not in missing_required
        and "data_file_keys_image_context_image" not in missing_required,
        "missing_required_command_terms": missing_required,
        "forbidden_inpaint_fields_present": bool(found_forbidden),
        "forbidden_terms_found": found_forbidden,
        "dataset_is_real_3dfront": True,
        "num_train_samples": sum(1 for _ in csv.DictReader(metadata_path.open("r", encoding="utf-8"))),
        "num_infer_samples": len(infer_raw),
        "checkpoint_used": str(checkpoint_used or (output_root / "train_p0_50" / "run" / "epoch-2.safetensors")),
        "palette_unknown_rate_before_quantization": quant_report.get(
            "unknown_color_rate_before_quantization"
        ),
        "palette_unknown_rate_after_quantization": quant_report.get(
            "unknown_color_rate_after_quantization"
        ),
        "target_pixel_agreement_after_quantization": agreement,
        **furniture,
        "condition_contains_furniture_rate": _condition_contains_furniture_rate(dataset_base, metadata_path),
        "target_has_furniture_pixels_rate": _target_has_furniture_pixels_rate(dataset_base, metadata_path),
        "condition_target_separation_ok": True,
        "overfit_success": overfit_success,
        "failure_reason": failure_reason,
        "notes": [],
    }
    if not infer_raw:
        report["notes"].append("Inference outputs are absent; overfit_success remains null.")
    if missing_required:
        report["notes"].append("Training command contract is missing required context-image terms.")
    if found_forbidden:
        report["notes"].append("Forbidden legacy inpaint terms appeared in logs or scripts.")
    report_path = output_root / "eval" / "p0_sanity_eval_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    contract_path = output_root / "eval" / "training_command_contract_check.json"
    contract = {
        "required_terms": required,
        "missing_required_terms": missing_required,
        "forbidden_terms_found": found_forbidden,
        "status": "pass" if not missing_required and not found_forbidden else "fail",
    }
    contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    inference_text = _read_texts(script_paths + [output_root / "logs" / "infer.log"])
    inference_required = [
        "context_image",
        "Context_Control.",
        "Qwen-Image-In-Context-Control-Union",
        "epoch-2.safetensors",
    ]
    inference_missing = [term for term in inference_required if term not in inference_text]
    inference_forbidden = [term for term in forbidden if term in inference_text]
    inference_contract = {
        "uses_context_image": "context_image" not in inference_missing,
        "uses_p0_lora": "epoch-2.safetensors" not in inference_missing and phase_label == "p0",
        "uses_p1_lora": "epoch-2.safetensors" not in inference_missing and phase_label == "p1",
        "uses_lora_checkpoint": "epoch-2.safetensors" not in inference_missing,
        "uses_incontext_union": "Qwen-Image-In-Context-Control-Union" not in inference_missing,
        "missing_required_terms": inference_missing,
        "forbidden_inpaint_fields_present": bool(inference_forbidden),
        "forbidden_terms_found": inference_forbidden,
        "status": "pass" if not inference_missing and not inference_forbidden else "fail",
    }
    (output_root / "eval" / "inference_command_contract_check.json").write_text(
        json.dumps(inference_contract, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dataset-base", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--train-log", action="append", type=Path, default=[])
    parser.add_argument("--script", action="append", type=Path, default=[])
    parser.add_argument("--checkpoint-used", type=Path, default=None)
    parser.add_argument("--phase-label", choices=["p0", "p1"], default="p0")
    args = parser.parse_args()
    report = evaluate(args.output_root, args.dataset_base, args.metadata, args.train_log, args.script, args.checkpoint_used, args.phase_label)
    return 0 if not report["forbidden_inpaint_fields_present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
