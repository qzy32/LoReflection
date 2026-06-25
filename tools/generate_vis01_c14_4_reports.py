#!/usr/bin/env python3
"""Generate VIS-01 C14.4 visual and code-audit reports from existing artifacts."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
DOCS = ROOT / "docs"
VIS_ROOT = ROOT / "outputs" / "manual_review" / "vis01_c14_4_effect_report"
ACTIONS = ["REMOVE", "REPLACE", "TRANSLATE", "ADD"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def abs_posix(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def md_table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    out = ["|" + "|".join(keys) + "|", "|" + "|".join(["---"] * len(keys)) + "|"]
    for row in rows:
        vals = []
        for key in keys:
            val = row.get(key, "")
            if isinstance(val, float):
                val = f"{val:.4f}"
            vals.append(str(val).replace("|", "/"))
        out.append("|" + "|".join(vals) + "|")
    return "\n".join(out)


def font_bundle() -> tuple[ImageFont.ImageFont, ImageFont.ImageFont, ImageFont.ImageFont]:
    try:
        return (
            ImageFont.truetype("arial.ttf", 18),
            ImageFont.truetype("arialbd.ttf", 20),
            ImageFont.truetype("arial.ttf", 14),
        )
    except Exception:
        fallback = ImageFont.load_default()
        return fallback, fallback, fallback


FONT, FONT_B, FONT_S = font_bundle()


def c14_dirs() -> dict[str, Path]:
    return {
        "REMOVE": ROOT / "outputs/manual_review/c14_4_palette_fixed_REMOVE_20/c13_overfit_REMOVE/step300_eval",
        "REPLACE": ROOT / "outputs/manual_review/c14_4_palette_fixed_REPLACE_20/c13_overfit_REPLACE/step300_eval",
        "TRANSLATE": ROOT / "outputs/manual_review/c14_4_palette_fixed_TRANSLATE_20/c13_overfit_TRANSLATE/step300_eval",
        "ADD": ROOT / "outputs/manual_review/c14_4_palette_fixed_ADD_20/c13_overfit_ADD/step300_eval",
        "MIXED": ROOT / "outputs/manual_review/c14_4_palette_fixed_MIXED_80/c13_overfit_MIXED/step300_eval",
    }


def sample_metrics(sample_dir: Path) -> dict[str, Any]:
    path = sample_dir / "sample_metrics.json"
    return load_json(path) if path.exists() else {}


def sample_records(action: str) -> list[dict[str, Any]]:
    root = c14_dirs()[action]
    if not root.exists():
        return []
    rows = []
    for sample_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        metrics = sample_metrics(sample_dir)
        if metrics:
            rows.append({"dir": sample_dir, "sample_id": sample_dir.name, "metrics": metrics})
    return rows


def infer_categories(metrics: dict[str, Any]) -> tuple[str, str]:
    prompt = metrics.get("prompt", "") or ""
    action = metrics.get("action", "")
    source, target = "unknown", "unknown"
    if action == "REMOVE":
        match = re.search(r"containing ([a-zA-Z0-9_]+)", prompt)
        if match:
            source, target = match.group(1), "floor/background"
    elif action == "ADD":
        match = re.search(r"one ([a-zA-Z0-9_]+)", prompt)
        if match:
            target = match.group(1)
    elif action == "TRANSLATE":
        match = re.search(r"one ([a-zA-Z0-9_]+)", prompt)
        if match:
            source = target = match.group(1)
    elif action == "REPLACE":
        match = re.search(r"replace ([a-zA-Z0-9_]+) with ([a-zA-Z0-9_]+)", prompt, re.I)
        if match:
            source, target = match.group(1), match.group(2)
    return source, target


def failure_reason(metrics: dict[str, Any]) -> str:
    if metrics.get("edit_success") is True:
        return "PASS: strict edit_success true"
    reasons = []
    if (metrics.get("allowed_label_violation_count") or 0) > 0:
        reasons.append("allowed-label violations")
    if (metrics.get("extra_component_count") or 0) > 0:
        reasons.append("extra components")
    if (metrics.get("masked_pixel_accuracy") or 0) < 0.95:
        reasons.append("masked reconstruction weak")
    if metrics.get("action_specific_iou") is not None and (metrics.get("action_specific_iou") or 0) < 0.85:
        reasons.append("action IoU below gate")
    if metrics.get("action") == "TRANSLATE" and metrics.get("new_region_target_present") is False:
        reasons.append("new region target missing")
    if metrics.get("action") in {"REMOVE", "REPLACE"} and metrics.get("source_removed_or_replaced") is False:
        reasons.append("source not cleared")
    return ", ".join(reasons) if reasons else "strict gate failed"


def wrap_text(text: str, draw: ImageDraw.ImageDraw, max_width: int, font: ImageFont.ImageFont) -> list[str]:
    words = str(text).split()
    lines, line = [], ""
    for word in words:
        cand = (line + " " + word).strip()
        if draw.textbbox((0, 0), cand, font=font)[2] <= max_width or not line:
            line = cand
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def make_sheet(record: dict[str, Any], out_path: Path) -> None:
    sample_dir = record["dir"]
    metrics = record["metrics"]
    panels = [
        ("I_bad", "I_bad.png"),
        ("I_target", "I_target.png"),
        ("control_mask", "control_mask.png"),
        ("raw_output", "raw_output.png"),
        ("snapped_output", "snapped_output.png"),
        ("copyback_output", "copyback_output.png"),
        ("diff_map", "diff_map.png"),
    ]
    cell_w, img_h, label_h, text_h = 190, 190, 28, 120
    width = cell_w * len(panels)
    canvas = Image.new("RGB", (width, label_h + img_h + text_h), "white")
    draw = ImageDraw.Draw(canvas)
    for idx, (label, filename) in enumerate(panels):
        x = idx * cell_w
        path = sample_dir / filename
        if path.exists():
            img = Image.open(path).convert("RGB").resize((cell_w, img_h), Image.Resampling.NEAREST)
        else:
            img = Image.new("RGB", (cell_w, img_h), (230, 230, 230))
            ImageDraw.Draw(img).text((10, 80), "MISSING", font=FONT, fill=(120, 0, 0))
        draw.rectangle([x, 0, x + cell_w - 1, canvas.height - 1], outline=(210, 210, 210))
        draw.text((x + 6, 6), label, font=FONT_B, fill=(0, 0, 0))
        canvas.paste(img, (x, label_h))
    source, target = infer_categories(metrics)
    lines = [
        f"action={metrics.get('action')} sample={metrics.get('sample_id', sample_dir.name)}",
        f"source={source} target={target}",
        f"masked_acc={metrics.get('masked_pixel_accuracy')} action_iou={metrics.get('action_specific_iou')} edit_success={metrics.get('edit_success')}",
        f"allowed_viol={metrics.get('allowed_label_violation_count')} extra_components={metrics.get('extra_component_count')}",
        f"failure={failure_reason(metrics)}",
    ]
    y = label_h + img_h + 6
    for line in lines:
        for wrapped in wrap_text(line, draw, width - 18, FONT_S)[:2]:
            draw.text((8, y), wrapped, font=FONT_S, fill=(0, 0, 0))
            y += 17
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def choose_samples(action: str) -> list[dict[str, Any]]:
    rows = sample_records(action)
    if action == "REMOVE":
        success = [row for row in rows if row["metrics"].get("edit_success")]
        fail = [row for row in rows if not row["metrics"].get("edit_success")]
        return success[:3] + sorted(fail, key=lambda row: row["metrics"].get("action_specific_iou") or 0)[:3]
    if action in {"REPLACE", "ADD"}:
        top = sorted(rows, key=lambda row: row["metrics"].get("action_specific_iou") or 0, reverse=True)[:3]
        bottom = sorted(rows, key=lambda row: row["metrics"].get("action_specific_iou") or 0)[:3]
        return top + bottom
    if action == "TRANSLATE":
        top = sorted(rows, key=lambda row: row["metrics"].get("action_specific_iou") or 0, reverse=True)[:3]
        bottom = sorted(
            rows,
            key=lambda row: (row["metrics"].get("new_region_target_present") is not False, row["metrics"].get("action_specific_iou") or 0),
        )[:3]
        return top + bottom
    return rows[:6]


def build_visual_index() -> list[dict[str, Any]]:
    expected = [
        "I_bad.png",
        "I_target.png",
        "control_mask.png",
        "raw_output.png",
        "snapped_output.png",
        "copyback_output.png",
        "sanitized_output.png",
        "diff_map.png",
        "overlay.png",
        "contact_sheet.png",
        "sample_metrics.json",
        "metrics.json",
        "sample_summary.json",
    ]
    rows = []
    for action, root in c14_dirs().items():
        if not root.exists():
            rows.append({"action": action, "sample_id": "__folder_missing__", "sample_dir": rel(root), "folder_exists": False})
            continue
        for sample_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            metrics = sample_metrics(sample_dir)
            row = {
                "action": action,
                "eval_step": "step300",
                "sample_id": sample_dir.name,
                "sample_dir": rel(sample_dir),
                "folder_exists": True,
                "metric_action": metrics.get("action", ""),
                "edit_success": metrics.get("edit_success", ""),
                "masked_pixel_accuracy": metrics.get("masked_pixel_accuracy", ""),
                "action_specific_iou": metrics.get("action_specific_iou", ""),
                "allowed_label_violation_count": metrics.get("allowed_label_violation_count", ""),
                "extra_component_count": metrics.get("extra_component_count", ""),
            }
            for filename in expected:
                row[filename] = rel(sample_dir / filename) if (sample_dir / filename).exists() else ""
            row["available_files"] = ";".join(sorted(p.name for p in sample_dir.iterdir() if p.is_file()))
            row["missing_expected"] = ";".join(filename for filename in expected if not (sample_dir / filename).exists())
            rows.append(row)
    write_json(REPORT_DIR / "vis01_c14_4_visual_artifact_index.json", {
        "schema_version": "vis01-visual-artifact-index-v1",
        "timestamp": datetime.now().isoformat(),
        "items": rows,
    })
    with (REPORT_DIR / "vis01_c14_4_visual_artifact_index.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = sorted(set().union(*(row.keys() for row in rows))) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def make_grid(paths: list[Path], out_path: Path, title: str) -> None:
    cells = []
    for path in paths:
        if not path.exists():
            continue
        img = Image.open(path).convert("RGB")
        img.thumbnail((560, 150), Image.Resampling.LANCZOS)
        cell = Image.new("RGB", (580, 185), "white")
        cell.paste(img, (10, 28))
        ImageDraw.Draw(cell).text((10, 6), path.stem[:70], font=FONT_S, fill=(0, 0, 0))
        cells.append(cell)
    cols = 2
    rows = max(1, math.ceil(len(cells) / cols))
    canvas = Image.new("RGB", (cols * 580, 40 + rows * 185), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 10), title, font=FONT_B, fill=(0, 0, 0))
    for idx, cell in enumerate(cells):
        canvas.paste(cell, ((idx % cols) * 580, 40 + (idx // cols) * 185))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def generate_visuals() -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    for name in ["REMOVE", "REPLACE", "TRANSLATE", "ADD", "MIXED", "contact_sheets", "html"]:
        (VIS_ROOT / name).mkdir(parents=True, exist_ok=True)
    contact_rows = []
    selected: dict[str, list[str]] = {}
    for action in ACTIONS:
        selected[action] = []
        seen: set[str] = set()
        for record in choose_samples(action):
            sample_id = record["sample_id"]
            if sample_id in seen:
                continue
            seen.add(sample_id)
            selected[action].append(sample_id)
            out_path = VIS_ROOT / action / f"{sample_id}_vis01_contact.png"
            make_sheet(record, out_path)
            shutil.copy2(out_path, VIS_ROOT / "contact_sheets" / f"{action}_{sample_id}.png")
            contact_rows.append({
                "action": action,
                "sample_id": sample_id,
                "path": rel(out_path),
                "metrics": record["metrics"],
                "failure_reason": failure_reason(record["metrics"]),
            })
    selected["MIXED"] = []
    for record in sample_records("MIXED"):
        sample_id = record["sample_id"]
        selected["MIXED"].append(sample_id)
        out_path = VIS_ROOT / "MIXED" / f"{sample_id}_vis01_contact.png"
        make_sheet(record, out_path)
        shutil.copy2(out_path, VIS_ROOT / "contact_sheets" / f"MIXED_{sample_id}.png")
        contact_rows.append({
            "action": "MIXED",
            "sample_id": sample_id,
            "path": rel(out_path),
            "metrics": record["metrics"],
            "failure_reason": failure_reason(record["metrics"]),
        })
    best_paths, fail_paths = [], []
    for action in ACTIONS:
        rows = sample_records(action)
        if not rows:
            continue
        best = max(rows, key=lambda row: (row["metrics"].get("edit_success") is True, row["metrics"].get("action_specific_iou") or 0))
        fail = min(rows, key=lambda row: (row["metrics"].get("edit_success") is True, row["metrics"].get("action_specific_iou") or 0))
        best_paths.append(VIS_ROOT / action / f"{best['sample_id']}_vis01_contact.png")
        fail_paths.append(VIS_ROOT / action / f"{fail['sample_id']}_vis01_contact.png")
    make_grid(best_paths, VIS_ROOT / "c14_4_four_action_overview.png", "C14.4 palette-fixed: best sampled examples by action")
    make_grid(fail_paths, VIS_ROOT / "c14_4_four_action_failure_examples.png", "C14.4 palette-fixed: failure examples by action")
    make_grid([ROOT / row["path"] for row in contact_rows if row["action"] == "MIXED"], VIS_ROOT / "c14_4_mixed_overview.png", "C14.4 MIXED_80 sampled visual examples")
    return contact_rows, selected


def metric_rows(result: dict[str, Any], single: dict[str, Any], mixed: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for action in ACTIONS:
        action_result = single["actions"][action]
        metrics = result["single_actions"][action]["metrics"]
        rows.append({
            "action": action,
            "rows": 20,
            "steps": action_result["steps"],
            "loss": action_result["loss"],
            "masked_accuracy": metrics["avg_masked_pixel_accuracy"],
            "action_iou": metrics["avg_action_specific_iou"],
            "edit_success": metrics["edit_success_rate"],
            "gate": action_result["gate"],
            "checkpoint": action_result["checkpoint"],
            "main_failure": "strict pass on 3/5 sampled eval; failures still extra components/allowed labels"
            if action == "REMOVE"
            else "nonzero IoU but strict gate blocked by reconstruction, extra components, or allowed labels",
        })
    rows.append({
        "action": "MIXED_80",
        "rows": 80,
        "steps": mixed["steps"],
        "loss": mixed["loss"],
        "masked_accuracy": result["mixed"]["metrics"]["avg_masked_pixel_accuracy"],
        "action_iou": result["mixed"]["metrics"]["avg_action_specific_iou"],
        "edit_success": result["mixed"]["metrics"]["edit_success_rate"],
        "gate": mixed["gate"],
        "checkpoint": mixed["checkpoint"],
        "main_failure": "sampled visual eval currently covers ADD rows only; strict edit_success remains 0",
    })
    return rows


def training_parameters() -> dict[str, Any]:
    return {
        "dataset_base_path": "/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v2_palette_fixed",
        "base_model": "Qwen/Qwen-Image transformer/text_encoder/vae from DiffSynth model pool",
        "controlnet": "DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint:model.safetensors",
        "batch_size": 1,
        "gradient_accumulation": 1,
        "effective_batch": 1,
        "learning_rate": "1e-4",
        "optimizer": "not explicitly set in C14.4 wrapper; DiffSynth runner default",
        "scheduler": "constant (DiffSynth parser default unless overridden)",
        "lora_rank": 32,
        "lora_alpha": "not explicitly set; add_lora_to_model defaults alpha=rank",
        "lora_dropout": "not explicitly set; PEFT default",
        "precision": "torch.bfloat16 pipeline load",
        "max_pixels": 262144,
        "seed": 4411,
        "gradient_checkpointing": "enabled",
        "num_workers": 0,
        "save_interval": 100,
        "eval_interval": "training validation disabled; external infer-action eval after step100 and step300",
        "extra_inputs": "blockwise_controlnet_image,blockwise_controlnet_inpaint_mask",
        "single_action_fixedsteps": "DATASET_REPEAT=1, NUM_EPOCHS=15, 20 rows -> 300 epoch-end steps",
        "mixed_fixedsteps": "DATASET_REPEAT=1, NUM_EPOCHS=4, 80 rows -> step-300 checkpoint during 320-step epoch end",
    }


def write_audit_reports(contact_rows: list[dict[str, Any]], selected: dict[str, list[str]], rows: list[dict[str, Any]]) -> None:
    ckpts = load_json(REPORT_DIR / "c14_4_checkpoint_list.json")
    params = training_parameters()
    config_paths = {
        "add": ROOT / "configs/c14_3_semantic_repair4_palette_fixed/add_20.yaml",
        "remove": ROOT / "configs/c14_3_semantic_repair4_palette_fixed/remove_20.yaml",
        "translate": ROOT / "configs/c14_3_semantic_repair4_palette_fixed/translate_20.yaml",
        "replace": ROOT / "configs/c14_3_semantic_repair4_palette_fixed/replace_20.yaml",
        "mixed_80": ROOT / "configs/c14_3_semantic_repair4_palette_fixed/mixed_80.yaml",
    }
    write_json(REPORT_DIR / "vis01_c14_4_visual_effect_report.json", {
        "schema_version": "vis01-c14-4-visual-effect-report-v1",
        "timestamp": datetime.now().isoformat(),
        "summary": rows,
        "selected_samples": selected,
        "contact_sheets": contact_rows,
        "warnings": ["MIXED_80 existing sampled visual eval contains only ADD rows; no inference-only rerun was launched in VIS-01."],
    })
    write_json(REPORT_DIR / "vis01_training_code_and_parameter_audit.json", {
        "schema_version": "vis01-training-code-and-parameter-audit-v1",
        "timestamp": datetime.now().isoformat(),
        "main_wrapper": "diffusion/train_diffsynth_qwen_inpaint_lora.sh",
        "per_action_scripts": [
            "scripts/c14_3_train_remove_20.sh",
            "scripts/c14_3_train_replace_20.sh",
            "scripts/c14_3_train_translate_20.sh",
            "scripts/c14_3_train_add_20.sh",
            "scripts/c14_3_train_mixed_80.sh",
            "scripts/c14_3_wait_and_run_palette_fixed.sh",
            "scripts/c14_4_wait_and_run_palette_fixed_clean_training.sh",
        ],
        "configs": {key: rel(path) for key, path in config_paths.items()},
        "remote_train_entry": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py",
        "remote_common_script": "/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v2_palette_fixed/_scripts/c14_3_train_common.sh",
        "metadata_files": {
            name: f"/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v2_palette_fixed/metadata_{name}.csv"
            for name in ["add", "remove", "translate", "replace", "mixed_80"]
        },
        "parameters": params,
        "checkpoint_paths": ckpts["checkpoints"],
        "notes": ["C14.4 valid run used fixedsteps override, not the older C14.3 epoch/repeat command."],
    })
    write_json(REPORT_DIR / "vis01_diffsynth_loss_function_audit.json", {
        "schema_version": "vis01-diffsynth-loss-function-audit-v1",
        "timestamp": datetime.now().isoformat(),
        "loss_file": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/diffsynth/diffusion/loss.py",
        "loss_function": "FlowMatchSFTLoss lines 5-28; mse_loss at line 26; scheduler training_weight at line 27",
        "train_entry": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py lines 49-56 and 88-94",
        "dataset_file": "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/diffsynth/core/data/unified_dataset.py lines 75-106",
        "extra_inputs": "training_module.py lines 299-316 maps blockwise_controlnet_image/mask into ControlNetInput under blockwise_controlnet_inputs",
        "target": "scheduler.training_target(input_latents, noise, timestep)",
        "objective": "Flow matching SFT diffusion objective: noised target latents -> model_fn -> MSE to scheduler target.",
        "mask_only_or_full_image": "No explicit mask-only loss found; training appears to optimize the DiffSynth/Qwen diffusion objective on the training image conditioned by control image and inpaint mask.",
        "mask_weighting": "No explicit mask-region loss weighting found in FlowMatchSFTLoss.",
        "trainable_modules": "LoRA adapters injected into dit; base modules frozen by freeze_except([]).",
        "base_model_frozen": True,
        "controlnet_frozen": True,
        "unknowns": ["Optimizer class is not explicit in C14.4 wrapper; review DiffSynth runner defaults if exact optimizer identity is needed."],
    })
    write_json(REPORT_DIR / "vis01_evaluation_code_audit.json", {
        "schema_version": "vis01-evaluation-code-audit-v1",
        "timestamp": datetime.now().isoformat(),
        "evaluator": "tools/evaluate_c13_semantic_repair4_outputs.py",
        "inference_wrapper": "infer-action subcommand loads QwenImagePipeline, loads LoRA into pipe.dit, runs conditioned inference, writes raw_output, snaps/copybacks, and computes metrics.",
        "raw_output": "direct model sample before palette snapping",
        "snapped_output": "nearest frozen-palette version of raw output",
        "copyback_output": "snapped output inside white mask copied onto I_bad while black mask is preserved",
        "sanitized_output": "not separately emitted in current C14.4 evaluator",
        "diff_map": "red pixels where copyback_output differs from I_target",
        "overlay": "not emitted by current evaluator",
        "edit_success_logic": "masked_pixel_accuracy >=0.95, nonmask_equality_after_copyback ==1.0, object_count_f1 >=0.95, allowed_label_violation_count ==0, and action_iou is None or >=0.85",
        "visualization_generation": "VIS-01 generated annotated sheets and overview PNGs.",
    })


def write_docs(rows: list[dict[str, Any]]) -> None:
    metrics_md = md_table(rows, ["action", "rows", "steps", "loss", "masked_accuracy", "action_iou", "edit_success", "gate", "main_failure"])
    overview = abs_posix(VIS_ROOT / "c14_4_four_action_overview.png")
    failure = abs_posix(VIS_ROOT / "c14_4_four_action_failure_examples.png")
    mixed = abs_posix(VIS_ROOT / "c14_4_mixed_overview.png")
    visual_md = f"""# VIS-01 C14.4 Visual Effect Report

## 1. What C14.4 Completed

C13 was a 3/action small overfit proof. C14.4 is different: it is the first palette-fixed 20/action medium clean diagnostic training run under the corrected evaluator/data/palette contract.

C14.4 trained ADD, REMOVE, TRANSLATE, and REPLACE for 300 steps each, then trained and evaluated MIXED_80. The current conclusion is PARTIAL: REMOVE is the best action with edit_success 0.60 on sampled evaluation, while REPLACE, TRANSLATE, ADD, and MIXED_80 have nonzero learning signal but strict edit_success 0.

![four-action overview]({overview})

## 2. Four-Action Metrics

{metrics_md}

## 3. How to Read the Visualizations

- I_bad: the bad input image the model receives as condition.
- I_target: the target image we hope the repair should become.
- control_mask: white means the model is allowed to repaint; black means preserve.
- raw_output: direct model output before palette snapping.
- snapped_output: raw output after colors are snapped to the frozen semantic palette.
- copyback_output: snapped pixels inside the mask copied onto I_bad, while black-mask regions are restored from I_bad.
- sanitized_output: this C14.4 evaluator does not emit a separate file; copyback_output is the final constrained output.
- diff_map: red marks where copyback_output differs from I_target.

For REMOVE, first check whether the source object is cleared. For REPLACE, check whether the source disappears and the target appears. For TRANSLATE, check whether old_region is cleared and new_region is generated. For ADD, check whether the target appears completely. If action_iou is high but edit_success is low, inspect extra_component_count and allowed_label_violation_count.

## 4. REMOVE Visual Summary

REMOVE often succeeds: three of five sampled step-300 rows pass strict edit_success. Failures still show extra components or allowed-label violations even when the source object is cleared.

Open: `{rel(VIS_ROOT / 'REMOVE')}`

## 5. REPLACE Visual Summary

REPLACE has nonzero target/action IoU but strict edit_success remains 0. Some rows remove the source and approximate the target, but allowed-label violations, extra components, or low masked reconstruction keep the strict gate closed.

Open: `{rel(VIS_ROOT / 'REPLACE')}`

## 6. TRANSLATE Visual Summary

TRANSLATE mostly preserves black-mask regions and often clears the old region, but new_region target generation is unstable. This is why several samples look half-right while edit_success remains 0.

Open: `{rel(VIS_ROOT / 'TRANSLATE')}`

## 7. ADD Visual Summary

ADD can produce target-like regions with high action_iou on some samples, but target completeness and extra fragments remain unstable. This explains high action_iou with edit_success 0.

Open: `{rel(VIS_ROOT / 'ADD')}`

## 8. MIXED_80 Visual Summary

MIXED_80 was trained and evaluated. The existing sampled visual folder contains ADD rows only because the evaluator used the first five rows of metadata_mixed_80. Treat the mixed visual page as a limited sampled view, not per-action mixed coverage.

![mixed overview]({mixed})

## 9. Failure Examples

![failure examples]({failure})

## 10. Conclusion

C14.4 proves the training chain and model learning signal are real under the corrected palette contract. It is not ready for 50/action or larger semantic_repair4 training. The next step is C15 action-specific diagnosis: checkpoint A/B, prompt ablation, mask ablation, and allowed-label / extra-component diagnosis.
"""
    (DOCS / "VIS01_C14_4_VISUAL_EFFECT_REPORT.md").write_text(visual_md, encoding="utf-8")
    params = training_parameters()
    ckpts = load_json(REPORT_DIR / "c14_4_checkpoint_list.json")
    (DOCS / "VIS01_TRAINING_CODE_AND_PARAMETER_AUDIT.md").write_text(f"""# VIS-01 Training Code and Parameter Audit

## Main Training Map

- `diffusion/train_diffsynth_qwen_inpaint_lora.sh`: local/general Qwen-DiffSynth LoRA training wrapper.
- `scripts/c14_3_train_remove_20.sh`, `scripts/c14_3_train_replace_20.sh`, `scripts/c14_3_train_translate_20.sh`, `scripts/c14_3_train_add_20.sh`, `scripts/c14_3_train_mixed_80.sh`: local stubs that call server-side generated scripts.
- `scripts/c14_4_wait_and_run_palette_fixed_clean_training.sh`: C14.4 fixed-step runner.
- Remote train entry: `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`.

## Metadata Contract

`image` = I_target, `blockwise_controlnet_image` = I_bad, `blockwise_controlnet_inpaint_mask` = control_mask, `prompt` = correction_prompt.

Server metadata paths: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v2_palette_fixed/metadata_add.csv`, `metadata_remove.csv`, `metadata_translate.csv`, `metadata_replace.csv`, and `metadata_mixed_80.csv`.

## Parameters Actually Used

```json
{json.dumps(params, ensure_ascii=False, indent=2)}
```

## Checkpoints

```json
{json.dumps(ckpts['checkpoints'], ensure_ascii=False, indent=2)}
```

## Unknown or Default Parameters

Optimizer, LoRA dropout, and some accelerator details are not explicitly set by the C14.4 wrapper; they use DiffSynth/PEFT defaults unless the remote runner sets them internally.
""", encoding="utf-8")
    (DOCS / "VIS01_DIFFSYNTH_LOSS_FUNCTION_EXPLANATION.md").write_text("""# VIS-01 DiffSynth Loss Function Explanation

## Where Loss Is Computed

The C14.4 train entry is `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`.

- `train.py` lines 49-56 maps task `sft` / `sft:train` to `FlowMatchSFTLoss`.
- `train.py` lines 88-94 runs pipeline units and then calls the selected loss.
- The actual loss function is `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/diffsynth/diffusion/loss.py`, `FlowMatchSFTLoss` lines 5-28.
- `loss.py` line 26 computes `torch.nn.functional.mse_loss(noise_pred.float(), training_target.float())`.
- `loss.py` line 27 multiplies by scheduler training weight.

## Objective

The training image `image = I_target` is encoded into latents. DiffSynth samples a random timestep, adds noise to those latents, asks the model to predict the scheduler training target, and applies MSE between prediction and target.

No explicit mask-only loss found; training appears to optimize the DiffSynth/Qwen diffusion objective on the training image conditioned by control image and inpaint mask.

## Input Flow

`UnifiedDataset` reads CSV rows. In `unified_dataset.py` lines 75-106, CSV metadata is loaded and `data_file_keys` are converted through image operators.

`training_module.py` lines 299-316 maps `blockwise_controlnet_image` and `blockwise_controlnet_inpaint_mask` into `ControlNetInput` under `blockwise_controlnet_inputs`.

`qwen_image.py` lines 514-526 preprocess control image and mask into blockwise ControlNet conditioning. Lines 784-808 inject blockwise ControlNet output into the DiT forward path.

## Trainable Modules

C14.4 passes `--lora_base_model dit` and does not pass `--trainable_models`. `training_module.py` line 239 freezes the pipeline, then lines 250-259 inject LoRA into `dit`. The blockwise ControlNet is not trained in C14.4.
""", encoding="utf-8")
    (DOCS / "VIS01_EVALUATION_AND_VISUALIZATION_CODE_GUIDE.md").write_text(f"""# VIS-01 Evaluation and Visualization Code Guide

The evaluator is `tools/evaluate_c13_semantic_repair4_outputs.py`.

- `raw_output.png`: direct model sample.
- `snapped_output.png`: nearest frozen-palette version of raw output.
- `copyback_output.png`: final constrained output; mask outside is copied back from I_bad.
- `sanitized_output.png`: not separately emitted in C14.4.
- `diff_map.png`: red difference pixels against I_target.
- `contact_sheet.png`: evaluator quick sheet; VIS-01 creates larger annotated sheets.

The strict gate requires masked pixel accuracy >= 0.95, nonmask equality after copyback = 1.0, object_count_f1 >= 0.95, no allowed-label violations, and action_iou >= 0.85 when applicable.

VIS-01 generated annotated contact sheets and overview figures under `{rel(VIS_ROOT)}`.
""", encoding="utf-8")


def write_html(contact_rows: list[dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    metrics_md = md_table(rows, ["action", "rows", "steps", "loss", "masked_accuracy", "action_iou", "edit_success", "gate", "main_failure"])
    cards = []
    for row in contact_rows:
        img_rel = os.path.relpath(ROOT / row["path"], VIS_ROOT).replace(os.sep, "/")
        metrics = row["metrics"]
        cards.append(
            f"<section><h3>{row['action']} - {row['sample_id']}</h3>"
            f"<img src='{img_rel}'>"
            f"<p>masked_acc={metrics.get('masked_pixel_accuracy')} action_iou={metrics.get('action_specific_iou')} "
            f"edit_success={metrics.get('edit_success')} allowed={metrics.get('allowed_label_violation_count')} "
            f"extra={metrics.get('extra_component_count')}</p><p>{row['failure_reason']}</p></section>"
        )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>VIS-01 C14.4 Visual Effect Report</title>
<style>body{{font-family:Arial,sans-serif;margin:24px;line-height:1.45}}img{{max-width:100%;border:1px solid #ccc}}section{{margin:24px 0;padding-bottom:18px;border-bottom:1px solid #ddd}}pre{{white-space:pre-wrap}}</style></head>
<body><h1>VIS-01 C14.4 Visual Effect Report</h1>
<p>C14.4 is the first palette-fixed 20/action clean diagnostic training result. It is PARTIAL, not final.</p>
<img src="c14_4_four_action_overview.png">
<h2>Metrics</h2><pre>{metrics_md}</pre>
<h2>Failure Examples</h2><img src="c14_4_four_action_failure_examples.png">
<h2>MIXED</h2><img src="c14_4_mixed_overview.png">
<h2>Contact Sheets</h2>{''.join(cards)}</body></html>
"""
    (VIS_ROOT / "index.html").write_text(html, encoding="utf-8")
    (VIS_ROOT / "html" / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    result = load_json(REPORT_DIR / "c14_4_palette_fixed_clean_training_result.json")
    single = load_json(REPORT_DIR / "c14_4_single_action_summary.json")
    mixed = load_json(REPORT_DIR / "c14_4_palette_fixed_MIXED_80.json")
    build_visual_index()
    contact_rows, selected = generate_visuals()
    rows = metric_rows(result, single, mixed)
    write_audit_reports(contact_rows, selected, rows)
    write_docs(rows)
    write_html(contact_rows, rows)
    print(json.dumps({
        "generated": [
            rel(DOCS / "VIS01_C14_4_VISUAL_EFFECT_REPORT.md"),
            rel(VIS_ROOT / "index.html"),
            rel(REPORT_DIR / "vis01_c14_4_visual_artifact_index.json"),
            rel(REPORT_DIR / "vis01_training_code_and_parameter_audit.json"),
            rel(REPORT_DIR / "vis01_diffsynth_loss_function_audit.json"),
            rel(REPORT_DIR / "vis01_evaluation_code_audit.json"),
        ],
        "contact_sheet_count": len(contact_rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
