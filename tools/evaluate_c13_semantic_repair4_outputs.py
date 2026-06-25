#!/usr/bin/env python3
"""Evaluate C13 semantic_repair4 Qwen/DiffSynth overfit checkpoints.

This script is intentionally self-contained so it can run both from the local
LoReflection checkout and from the A800 server checkout.  It does not modify
DiffSynth; it only loads existing LoRA checkpoints, runs inference, snaps output
to the frozen palette, applies copyback, and reports small-batch overfit metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


ACTION_META = {
    "ADD": "metadata_add.csv",
    "REMOVE": "metadata_remove.csv",
    "TRANSLATE": "metadata_translate.csv",
    "REPLACE": "metadata_replace.csv",
    "MIXED": "metadata_mixed.csv",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_palette(repo: Path) -> tuple[list[str], np.ndarray, dict[str, int]]:
    palette_path = repo / "artifacts/semantic_registry_v2/palette_frozen.json"
    data = load_json(palette_path)
    colors = data["colors"]
    names = list(colors.keys())
    arr = np.array([colors[name] for name in names], dtype=np.uint8)
    return names, arr, {name: idx for idx, name in enumerate(names)}


def image_to_ids(img: Image.Image, palette: np.ndarray) -> np.ndarray:
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    flat = arr.reshape(-1, 3)
    diff = flat[:, None, :] - palette.astype(np.int16)[None, :, :]
    dist2 = np.sum(diff * diff, axis=2)
    ids = np.argmin(dist2, axis=1).astype(np.int16)
    return ids.reshape(arr.shape[:2])


def snap_to_palette(img: Image.Image, palette: np.ndarray) -> tuple[Image.Image, dict[str, float]]:
    arr = np.asarray(img.convert("RGB"), dtype=np.int32)
    flat = arr.reshape(-1, 3)
    pal = palette.astype(np.int32)
    diff = flat[:, None, :] - pal[None, :, :]
    dist2 = np.sum(diff * diff, axis=2)
    nearest = np.argmin(dist2, axis=1)
    dist = np.sqrt(np.min(dist2, axis=1).astype(np.float64))
    snapped = palette[nearest].reshape(arr.shape).astype(np.uint8)
    exact = np.any(np.all(flat[:, None, :] == pal[None, :, :], axis=2), axis=1)
    stats = {
        "palette_valid_pixel_ratio": float(np.mean(exact)),
        "nearest_palette_distance_mean": float(np.mean(dist)),
        "nearest_palette_distance_p95": float(np.percentile(dist, 95)),
    }
    return Image.fromarray(snapped, mode="RGB"), stats


def binary_mask(mask_img: Image.Image) -> np.ndarray:
    return np.asarray(mask_img.convert("L")) > 127


def polygon_mask(size: tuple[int, int], points: list[list[int]] | list[tuple[int, int]]) -> np.ndarray:
    im = Image.new("L", size, 0)
    if len(points) >= 3:
        ImageDraw.Draw(im).polygon([tuple(map(int, p)) for p in points], fill=255)
    return np.asarray(im) > 127


def component_masks_from_spec(mask_spec: dict[str, Any], role: str) -> np.ndarray | None:
    size = tuple(mask_spec.get("image_size_px", [512, 512]))
    out = np.zeros((size[1], size[0]), dtype=bool)
    found = False
    for comp in mask_spec.get("components", []):
        if comp.get("component_role") != role:
            continue
        geom_type = comp.get("geometry_type")
        geom = comp.get("geometry", {})
        local = None
        if geom_type in {"polygon", "footprint"}:
            pts = geom.get("polygon_px") or geom.get("footprint_px")
            if pts:
                local = polygon_mask(size, pts)
        elif geom_type == "bbox":
            bbox = geom.get("bbox_px")
            if bbox and len(bbox) == 4:
                local = np.zeros((size[1], size[0]), dtype=bool)
                x1, y1, x2, y2 = [int(v) for v in bbox]
                local[max(0, y1):min(size[1], y2), max(0, x1):min(size[0], x2)] = True
        if local is not None:
            out |= local
            found = True
    return out if found else None


def connected_components(mask: np.ndarray, min_area: int = 4) -> list[dict[str, Any]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps: list[dict[str, Any]] = []
    for y in range(h):
        xs = np.where(mask[y] & ~seen[y])[0]
        for x0 in xs:
            if seen[y, x0] or not mask[y, x0]:
                continue
            q = deque([(x0, y)])
            seen[y, x0] = True
            pts = []
            while q:
                x, yy = q.popleft()
                pts.append((x, yy))
                for nx, ny in ((x + 1, yy), (x - 1, yy), (x, yy + 1), (x, yy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((nx, ny))
            if len(pts) >= min_area:
                arr = np.array(pts)
                comps.append(
                    {
                        "area": int(len(pts)),
                        "bbox": [
                            int(arr[:, 0].min()),
                            int(arr[:, 1].min()),
                            int(arr[:, 0].max()) + 1,
                            int(arr[:, 1].max()) + 1,
                        ],
                        "centroid": [float(arr[:, 0].mean()), float(arr[:, 1].mean())],
                    }
                )
    return comps


def component_counts(ids: np.ndarray, names: list[str], min_area: int = 16) -> dict[int, int]:
    excluded = {"void", "floor", "door", "window", "wall", "room_boundary", "boundary"}
    counts: dict[int, int] = {}
    for sid in np.unique(ids):
        name = names[int(sid)] if int(sid) < len(names) else str(int(sid))
        if name in excluded:
            continue
        comps = connected_components(ids == sid, min_area=min_area)
        if comps:
            counts[int(sid)] = len(comps)
    return counts


def count_f1(pred: dict[int, int], target: dict[int, int]) -> tuple[float, int, int, int]:
    cats = set(pred) | set(target)
    tp = sum(min(pred.get(c, 0), target.get(c, 0)) for c in cats)
    pred_total = sum(pred.values())
    target_total = sum(target.values())
    denom = pred_total + target_total
    return (float(2 * tp / denom) if denom else 1.0, int(tp), int(pred_total), int(target_total))


def iou_for_id(pred_ids: np.ndarray, target_ids: np.ndarray, semantic_id: int, region: np.ndarray | None = None) -> float:
    p = pred_ids == semantic_id
    t = target_ids == semantic_id
    if region is not None:
        p &= region
        t &= region
    union = p | t
    if not union.any():
        return 1.0
    return float((p & t).sum() / union.sum())


def exact_rgb_accuracy(pred: Image.Image, target: Image.Image, region: np.ndarray) -> float:
    pa = np.asarray(pred.convert("RGB"))
    ta = np.asarray(target.convert("RGB"))
    if not region.any():
        return 1.0
    return float(np.all(pa[region] == ta[region], axis=1).mean())


def make_contact_sheet(paths: list[tuple[str, Path]], out_path: Path) -> None:
    cells = []
    for label, path in paths:
        img = Image.open(path).convert("RGB").resize((256, 256))
        cell = Image.new("RGB", (256, 286), "white")
        cell.paste(img, (0, 30))
        d = ImageDraw.Draw(cell)
        d.text((8, 8), label, fill=(0, 0, 0))
        cells.append(cell)
    sheet = Image.new("RGB", (256 * len(cells), 286), "white")
    for idx, cell in enumerate(cells):
        sheet.paste(cell, (idx * 256, 0))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def evaluate_sample(
    row: dict[str, str],
    sample_out: Path,
    palette: np.ndarray,
    names: list[str],
    action: str,
) -> dict[str, Any]:
    bad = Image.open(row["blockwise_controlnet_image"]).convert("RGB").resize((512, 512))
    target = Image.open(row["image"]).convert("RGB").resize((512, 512))
    mask_img = Image.open(row["blockwise_controlnet_inpaint_mask"]).convert("RGB").resize((512, 512))
    raw = Image.open(sample_out / "raw_output.png").convert("RGB").resize((512, 512))
    snapped, raw_palette_stats = snap_to_palette(raw, palette)
    mask = binary_mask(mask_img)
    bad_arr = np.asarray(bad)
    snapped_arr = np.asarray(snapped)
    copy = bad_arr.copy()
    copy[mask] = snapped_arr[mask]
    copy_img = Image.fromarray(copy, mode="RGB")

    snapped.save(sample_out / "snapped_output.png")
    copy_img.save(sample_out / "copyback_output.png")

    diff = np.zeros_like(copy)
    target_arr = np.asarray(target)
    diff_mask = np.any(copy != target_arr, axis=2)
    diff[diff_mask] = [255, 0, 0]
    Image.fromarray(diff, mode="RGB").save(sample_out / "diff_map.png")

    repairplan_path = Path(row["image"]).parent / "repairplan_current.json"
    plan = load_json(repairplan_path)
    mask_spec = plan.get("mask_spec") or {}
    delta = plan.get("target_state_delta") or {}
    target_id = delta.get("target_semantic_id")
    source_id = delta.get("source_semantic_id")
    allowed = set()
    for comp in mask_spec.get("components", []):
        allowed.update(int(x) for x in comp.get("allowed_labels", []) if x is not None)

    copy_ids = image_to_ids(copy_img, palette)
    target_ids = image_to_ids(target, palette)
    raw_ids = image_to_ids(raw, palette)

    pred_counts = component_counts(copy_ids, names)
    target_counts = component_counts(target_ids, names)
    oc_f1, oc_tp, oc_pred, oc_target = count_f1(pred_counts, target_counts)

    allowed_violations = 0
    if allowed and mask.any():
        allowed_violations = int(np.sum(mask & ~np.isin(copy_ids, list(allowed))))

    metrics: dict[str, Any] = {
        "sample_id": Path(row["image"]).parent.name,
        "action": action,
        "prompt": row.get("prompt", "")[:240],
        "masked_pixel_accuracy": exact_rgb_accuracy(copy_img, target, mask),
        "nonmask_equality_after_copyback": exact_rgb_accuracy(copy_img, bad, ~mask),
        "palette_validity_raw": raw_palette_stats["palette_valid_pixel_ratio"],
        "palette_validity_snapped": 1.0,
        "nearest_palette_distance_mean_raw": raw_palette_stats["nearest_palette_distance_mean"],
        "nearest_palette_distance_p95_raw": raw_palette_stats["nearest_palette_distance_p95"],
        "object_count_f1": oc_f1,
        "instance_precision": float(oc_tp / oc_pred) if oc_pred else 1.0,
        "instance_recall": float(oc_tp / oc_target) if oc_target else 1.0,
        "instance_f1": oc_f1,
        "extra_component_count": int(sum(max(0, pred_counts.get(c, 0) - target_counts.get(c, 0)) for c in set(pred_counts) | set(target_counts))),
        "allowed_label_violation_count": allowed_violations,
        "raw_unique_palette_ids_after_nearest": int(len(np.unique(raw_ids))),
        "copyback_unique_palette_ids": int(len(np.unique(copy_ids))),
    }

    if target_id is not None:
        target_id = int(target_id)
        metrics["target_object_iou"] = iou_for_id(copy_ids, target_ids, target_id)
        metrics["target_object_iou_inside_mask"] = iou_for_id(copy_ids, target_ids, target_id, mask)
    else:
        metrics["target_object_iou"] = None
        metrics["target_object_iou_inside_mask"] = None

    if source_id is not None:
        source_id = int(source_id)
        metrics["source_object_iou"] = iou_for_id(copy_ids, target_ids, source_id)
        metrics["source_remaining_pixels_inside_mask"] = int(np.sum(mask & (copy_ids == source_id)))
    else:
        metrics["source_object_iou"] = None
        metrics["source_remaining_pixels_inside_mask"] = None

    if action == "REMOVE":
        floor_id = 1
        metrics["white_region_floor_or_target_accuracy"] = exact_rgb_accuracy(copy_img, target, mask)
        metrics["source_removed_or_replaced"] = bool(metrics.get("source_remaining_pixels_inside_mask", 0) == 0)
    if action == "TRANSLATE":
        old_region = component_masks_from_spec(mask_spec, "old_region")
        new_region = component_masks_from_spec(mask_spec, "new_region")
        if target_id is not None and old_region is not None:
            metrics["old_region_target_pixels"] = int(np.sum(old_region & (copy_ids == target_id)))
            metrics["old_region_cleared"] = bool(metrics["old_region_target_pixels"] == 0)
        if target_id is not None and new_region is not None:
            tgt_pixels = int(np.sum(new_region & (target_ids == target_id)))
            pred_pixels = int(np.sum(new_region & (copy_ids == target_id)))
            metrics["new_region_target_present"] = bool(tgt_pixels > 0 and pred_pixels / max(1, tgt_pixels) >= 0.85)
    if action == "REPLACE":
        metrics["source_removed_or_replaced"] = bool(metrics.get("source_remaining_pixels_inside_mask", 0) == 0)

    action_iou = metrics.get("target_object_iou")
    if action == "REMOVE":
        action_iou = metrics["masked_pixel_accuracy"]
    metrics["action_specific_iou"] = action_iou
    metrics["edit_success"] = bool(
        metrics["masked_pixel_accuracy"] >= 0.95
        and metrics["nonmask_equality_after_copyback"] == 1.0
        and metrics["object_count_f1"] >= 0.95
        and allowed_violations == 0
        and (action_iou is None or action_iou >= 0.85)
    )

    make_contact_sheet(
        [
            ("I_bad", sample_out / "I_bad.png"),
            ("mask", sample_out / "control_mask.png"),
            ("I_target", sample_out / "I_target.png"),
            ("raw", sample_out / "raw_output.png"),
            ("snapped", sample_out / "snapped_output.png"),
            ("copyback", sample_out / "copyback_output.png"),
            ("diff", sample_out / "diff_map.png"),
        ],
        sample_out / "contact_sheet.png",
    )
    write_json(sample_out / "sample_metrics.json", metrics)
    return metrics


def infer_action(args: argparse.Namespace) -> None:
    # Import DiffSynth lazily so non-inference commands can run in a light env.
    import torch
    from diffsynth.pipelines.qwen_image import ControlNetInput, ModelConfig, QwenImagePipeline

    repo = Path(args.repo)
    names, palette, _ = load_palette(repo)
    meta_path = Path(args.metadata) if args.metadata else repo / "outputs/semantic_repair4_overfit_dataset_v1" / ACTION_META[args.action]
    out_root = Path(args.out_root) / f"c13_overfit_{args.action}" / args.run_name
    out_root.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(meta_path.open(newline="", encoding="utf-8")))
    lora_path = Path(args.lora)

    os.environ.setdefault("DIFFSYNTH_MODEL_BASE_PATH", "/wuqingyaoa800/qiuziyan/DiffSynth-Studio/models")
    os.environ.setdefault("DIFFSYNTH_SKIP_DOWNLOAD", "true")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    pipe = QwenImagePipeline.from_pretrained(
        torch_dtype=torch.bfloat16,
        device="cuda",
        model_configs=[
            ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="transformer/diffusion_pytorch_model*.safetensors"),
            ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="text_encoder/model*.safetensors"),
            ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="vae/diffusion_pytorch_model.safetensors"),
            ModelConfig(model_id="DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint", origin_file_pattern="model.safetensors"),
        ],
        tokenizer_config=ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="tokenizer/"),
    )
    pipe.load_lora(pipe.dit, str(lora_path))

    metrics = []
    for idx, row in enumerate(rows[: args.max_rows]):
        sample_id = Path(row["image"]).parent.name
        sample_out = out_root / sample_id
        sample_out.mkdir(parents=True, exist_ok=True)
        bad = Image.open(row["blockwise_controlnet_image"]).convert("RGB").resize((512, 512))
        target = Image.open(row["image"]).convert("RGB").resize((512, 512))
        mask = Image.open(row["blockwise_controlnet_inpaint_mask"]).convert("RGB").resize((512, 512))
        bad.save(sample_out / "I_bad.png")
        target.save(sample_out / "I_target.png")
        mask.save(sample_out / "control_mask.png")
        raw = pipe(
            row["prompt"],
            seed=args.seed + idx,
            input_image=bad,
            inpaint_mask=mask,
            blockwise_controlnet_inputs=[ControlNetInput(image=bad, inpaint_mask=mask)],
            num_inference_steps=args.inference_steps,
            height=512,
            width=512,
        )
        raw.convert("RGB").resize((512, 512)).save(sample_out / "raw_output.png")
        plan_action = args.action
        plan_path = Path(row["image"]).parent / "repairplan_current.json"
        if plan_path.exists():
            try:
                plan_action = load_json(plan_path).get("action_type") or args.action
            except Exception:
                plan_action = args.action
        metrics.append(evaluate_sample(row, sample_out, palette, names, plan_action))

    summary = summarize_metrics(args.action, metrics)
    summary.update(
        {
            "schema_version": "c13-action-inference-eval-v1",
            "action": args.action,
            "lora": str(lora_path),
            "metadata": str(meta_path),
            "out_root": str(out_root),
            "rows": len(metrics),
            "inference_steps": args.inference_steps,
            "seed": args.seed,
            "metrics": metrics,
        }
    )
    write_json(out_root / "metrics_by_checkpoint.json", summary)
    write_csv(out_root / "metrics_by_checkpoint.csv", metrics)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def eval_existing(args: argparse.Namespace) -> None:
    repo = Path(args.repo)
    names, palette, _ = load_palette(repo)
    meta_path = Path(args.metadata) if args.metadata else repo / "outputs/semantic_repair4_overfit_dataset_v1" / ACTION_META[args.action]
    out_root = Path(args.out_root) / f"c13_overfit_{args.action}" / args.run_name
    rows = list(csv.DictReader(meta_path.open(newline="", encoding="utf-8")))
    metrics = []
    for row in rows[: args.max_rows]:
        sample_id = Path(row["image"]).parent.name
        sample_out = out_root / sample_id
        if not (sample_out / "raw_output.png").exists():
            raise FileNotFoundError(sample_out / "raw_output.png")
        # Ensure the source triplet exists in the review folder.
        for src_key, dst_name in [
            ("blockwise_controlnet_image", "I_bad.png"),
            ("image", "I_target.png"),
            ("blockwise_controlnet_inpaint_mask", "control_mask.png"),
        ]:
            dst = sample_out / dst_name
            if not dst.exists():
                Image.open(row[src_key]).convert("RGB").resize((512, 512)).save(dst)
        metrics.append(evaluate_sample(row, sample_out, palette, names, args.action))
    summary = summarize_metrics(args.action, metrics)
    summary.update(
        {
            "schema_version": "c13-action-existing-output-eval-v1",
            "action": args.action,
            "metadata": str(meta_path),
            "out_root": str(out_root),
            "rows": len(metrics),
            "metrics": metrics,
        }
    )
    write_json(out_root / "metrics_by_checkpoint.json", summary)
    write_csv(out_root / "metrics_by_checkpoint.csv", metrics)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def summarize_metrics(action: str, metrics: list[dict[str, Any]]) -> dict[str, Any]:
    if not metrics:
        return {"gate": "SINGLE_ACTION_FAIL", "reason": "no_metrics"}
    keys = [
        "masked_pixel_accuracy",
        "nonmask_equality_after_copyback",
        "palette_validity_raw",
        "palette_validity_snapped",
        "target_object_iou",
        "target_object_iou_inside_mask",
        "object_count_f1",
        "instance_precision",
        "instance_recall",
        "instance_f1",
        "allowed_label_violation_count",
        "extra_component_count",
        "action_specific_iou",
    ]
    avg: dict[str, float | None] = {}
    for key in keys:
        vals = [m.get(key) for m in metrics if isinstance(m.get(key), (int, float))]
        avg[f"avg_{key}"] = float(np.mean(vals)) if vals else None
    pass_count = sum(1 for m in metrics if m.get("edit_success"))
    avg["edit_success_count"] = pass_count
    avg["edit_success_rate"] = float(pass_count / len(metrics))
    all_basic = (
        pass_count == len(metrics)
        and all(m.get("nonmask_equality_after_copyback") == 1.0 for m in metrics)
        and all((m.get("palette_validity_snapped") or 0) >= 0.99 for m in metrics)
    )
    if all_basic:
        gate = "SINGLE_ACTION_PASS"
    elif any((m.get("action_specific_iou") or 0) >= 0.5 or (m.get("masked_pixel_accuracy") or 0) >= 0.5 for m in metrics):
        gate = "SINGLE_ACTION_PARTIAL"
    else:
        gate = "SINGLE_ACTION_FAIL"
    avg["gate"] = gate
    return avg


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_train(args: argparse.Namespace) -> None:
    root = Path(args.train_root)
    out_reports = Path(args.reports)
    out_reports.mkdir(parents=True, exist_ok=True)
    actions = ["ADD", "REMOVE", "TRANSLATE", "REPLACE", "MIXED"]
    summary: dict[str, Any] = {"schema_version": "c13-train-100step-summary-v1", "actions": {}}
    all_rows: list[dict[str, Any]] = []
    for action in actions:
        run_dir = root / action / args.run_name
        metrics_path = run_dir / "train_metrics.jsonl"
        records = []
        if metrics_path.exists():
            for line in metrics_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        losses = [float(r["loss"]) for r in records if "loss" in r]
        steps = [int(r.get("step", i + 1)) for i, r in enumerate(records) if "loss" in r]
        checkpoints = sorted(str(p) for p in run_dir.glob("*.safetensors"))
        action_summary = {
            "action": action,
            "run_dir": str(run_dir),
            "metrics_jsonl": str(metrics_path),
            "steps_recorded": len(losses),
            "last_step": steps[-1] if steps else None,
            "loss_first": losses[0] if losses else None,
            "loss_last": losses[-1] if losses else None,
            "loss_min": min(losses) if losses else None,
            "loss_mean": float(np.mean(losses)) if losses else None,
            "checkpoints": checkpoints,
            "checkpoint_count": len(checkpoints),
            "status": "TRAINED_100_STEPS" if any("step-100" in p for p in checkpoints) else "INCOMPLETE",
        }
        summary["actions"][action] = action_summary
        loss_rows = [{"action": action, "step": s, "loss": l} for s, l in zip(steps, losses)]
        all_rows.extend(loss_rows)
        write_csv(out_reports / f"c13_loss_curve_{action}.csv", loss_rows)
        draw_loss_plot(loss_rows, out_reports / f"c13_loss_curve_{action}.png")
    write_json(out_reports / "c13_semantic_repair4_100step_training_summary.json", summary)
    write_csv(out_reports / "c13_semantic_repair4_100step_loss_curves.csv", all_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def draw_loss_plot(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (900, 420), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([60, 30, 860, 360], outline=(0, 0, 0))
    if rows:
        xs = [float(r["step"]) for r in rows]
        ys = [float(r["loss"]) for r in rows]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        if math.isclose(x0, x1):
            x1 = x0 + 1
        if math.isclose(y0, y1):
            y1 = y0 + 1
        pts = []
        for x, y in zip(xs, ys):
            px = 60 + (x - x0) / (x1 - x0) * 800
            py = 360 - (y - y0) / (y1 - y0) * 330
            pts.append((px, py))
        if len(pts) >= 2:
            d.line(pts, fill=(30, 90, 200), width=2)
        for px, py in pts[:: max(1, len(pts) // 30)]:
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(30, 90, 200))
        d.text((70, 12), f"loss min={y0:.6f} max={y1:.6f}", fill=(0, 0, 0))
        d.text((760, 370), f"step {int(x0)}-{int(x1)}", fill=(0, 0, 0))
    else:
        d.text((360, 190), "no loss records", fill=(0, 0, 0))
    img.save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("infer-action")
    p.add_argument("--repo", default="/wuqingyaoa800/qiuziyan/LoReflection")
    p.add_argument("--action", choices=list(ACTION_META), required=True)
    p.add_argument("--metadata")
    p.add_argument("--lora", required=True)
    p.add_argument("--out-root", default="/wuqingyaoa800/qiuziyan/LoReflection/outputs/manual_review")
    p.add_argument("--run-name", default="step100_eval")
    p.add_argument("--max-rows", type=int, default=3)
    p.add_argument("--inference-steps", type=int, default=12)
    p.add_argument("--seed", type=int, default=1300)
    p.set_defaults(func=infer_action)

    p = sub.add_parser("eval-existing")
    p.add_argument("--repo", default="/wuqingyaoa800/qiuziyan/LoReflection")
    p.add_argument("--action", choices=list(ACTION_META), required=True)
    p.add_argument("--metadata")
    p.add_argument("--out-root", default="/wuqingyaoa800/qiuziyan/LoReflection/outputs/manual_review")
    p.add_argument("--run-name", default="step100_eval")
    p.add_argument("--max-rows", type=int, default=3)
    p.set_defaults(func=eval_existing)

    p = sub.add_parser("summarize-train")
    p.add_argument("--train-root", default="/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_overfit_v1")
    p.add_argument("--run-name", default="run_100steps")
    p.add_argument("--reports", default="/wuqingyaoa800/qiuziyan/LoReflection/reports")
    p.set_defaults(func=summarize_train)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
