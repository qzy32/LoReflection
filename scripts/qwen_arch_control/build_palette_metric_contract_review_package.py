from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from loreflection.qwen_arch_control.prompt_labels.audit_metric_transform_contract import (
    audit_metric_transform_contract,
    resolve_architecture_path,
)
from loreflection.qwen_arch_control.prompt_labels.audit_palette_contract import (
    audit_metadata_palette_contract,
)
from loreflection.qwen_arch_control.prompt_labels.audit_rule_template_prompt_correctness import (
    audit_rule_template_prompt_correctness,
)
from loreflection.qwen_arch_control.prompt_labels.palette_contract import (
    get_active_palette_entries,
    load_palette_contract,
)


PREFERRED_SAMPLE_ID = "36c96aa6-a318-4212-aecc-22a206d7b217_room_00"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _required_counts(goal: dict[str, Any]) -> dict[str, int]:
    if isinstance(goal.get("required_counts"), dict):
        return {str(k): int(v) for k, v in goal["required_counts"].items()}
    counts: dict[str, int] = {}
    for slot in goal.get("furniture_slots", []):
        if not isinstance(slot, dict):
            continue
        cat = slot.get("category") or slot.get("semantic_category")
        count = int(slot.get("count") or slot.get("required_count") or 1)
        if cat:
            counts[str(cat)] = counts.get(str(cat), 0) + count
    return counts


def _pick_row(rows: list[dict[str, str]], sample_id: str) -> dict[str, str]:
    for row in rows:
        if row.get("sample_id") == sample_id:
            return row
    for row in rows:
        if "living" in row.get("prompt", "").lower():
            return row
    if not rows:
        raise FileNotFoundError("metadata has no rows")
    return rows[0]


def _side_by_side(paths: list[Path], labels: list[str], output: Path) -> None:
    images = [Image.open(path).convert("RGB") for path in paths if path.exists()]
    if not images:
        return
    w, h = images[0].size
    label_h = 26
    canvas = Image.new("RGB", (w * len(images), h + label_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    for i, image in enumerate(images):
        if image.size != (w, h):
            image = image.resize((w, h), Image.Resampling.NEAREST)
        canvas.paste(image, (i * w, label_h))
        draw.text((i * w + 4, 6), labels[i], fill=(0, 0, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def _legend(target: Path, entries: dict[str, list[int]], output: Path) -> None:
    base = Image.open(target).convert("RGB")
    swatch_w = 260
    row_h = 24
    canvas = Image.new("RGB", (base.width + swatch_w, max(base.height, row_h * max(1, len(entries)) + 8)), (255, 255, 255))
    canvas.paste(base, (0, 0))
    draw = ImageDraw.Draw(canvas)
    x0 = base.width + 8
    for i, (name, rgb) in enumerate(sorted(entries.items())):
        y = 8 + i * row_h
        draw.rectangle((x0, y, x0 + 18, y + 18), fill=tuple(rgb))
        draw.text((x0 + 26, y + 3), f"{name}: {rgb}", fill=(0, 0, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def build_review_package(
    dataset_base: Path,
    metadata_path: Path,
    output_root: Path,
    report_root: Path,
    sample_id: str,
    quantized_dir: Path | None,
    raw_pred_dir: Path | None,
    c2rgb_path: Path,
) -> dict[str, Any]:
    rows = list(csv.DictReader(metadata_path.open(encoding="utf-8")))
    row = _pick_row(rows, sample_id)
    sid = row["sample_id"]
    review = report_root / "sample_training_data_review"
    review.mkdir(parents=True, exist_ok=True)

    context_src = dataset_base / row["context_image"]
    target_src = dataset_base / row["image"]
    goal_src = dataset_base / row["goal_lostate"]
    pkg_src = dataset_base / row["prompt_package"]
    arch_src = resolve_architecture_path(dataset_base, row)

    shutil.copy2(context_src, review / "context_image.png")
    shutil.copy2(target_src, review / "target_semantic.png")
    shutil.copy2(goal_src, review / "goal_lostate.json")
    shutil.copy2(pkg_src, review / "prompt_package.json")

    goal = _read_json(goal_src)
    pkg = _read_json(pkg_src)
    arch = _read_json(arch_src) if arch_src and arch_src.exists() else {}
    transform = arch.get("metric_transform", {})
    _write_json(review / "metric_transform.json", transform)

    palette = load_palette_contract(c2rgb_path)
    active = pkg.get("active_palette_entries")
    if not isinstance(active, dict) or not active:
        active = get_active_palette_entries(_required_counts(goal), palette["c2rgb"])
    _write_json(review / "palette_entries.json", active)

    _side_by_side(
        [review / "context_image.png", review / "target_semantic.png"],
        ["context_image", "target_semantic"],
        review / "side_by_side_context_target.png",
    )
    _legend(review / "target_semantic.png", active, review / "target_with_palette_legend.png")

    pred_raw = None
    pred_quant = None
    if raw_pred_dir:
        candidate = raw_pred_dir / f"{sid}_raw.png"
        if candidate.exists():
            shutil.copy2(candidate, review / "pred_raw.png")
            pred_raw = review / "pred_raw.png"
    if quantized_dir:
        candidate = quantized_dir / f"{sid}_quantized.png"
        if candidate.exists():
            shutil.copy2(candidate, review / "pred_quantized.png")
            pred_quant = review / "pred_quantized.png"
    if pred_raw and pred_quant:
        _side_by_side(
            [review / "context_image.png", review / "target_semantic.png", pred_raw, pred_quant],
            ["context", "target", "pred_raw", "pred_quantized"],
            review / "side_by_side_context_target_pred.png",
        )

    record = {
        "sample_id": sid,
        "metadata_source": metadata_path.as_posix(),
        "image": row["image"],
        "context_image": row["context_image"],
        "prompt": row["prompt"],
        "compiled_prompt": pkg.get("compiled_prompt") or pkg.get("compiled_text_prompt") or row["prompt"],
        "user_intent_prompt": pkg.get("user_intent_prompt"),
        "architecture_control_prompt": pkg.get("architecture_control_prompt"),
        "palette_control_prompt": pkg.get("palette_control_prompt"),
        "required_counts": _required_counts(goal),
        "pairwise_constraints": goal.get("pairwise_constraints", []),
        "global_constraints": goal.get("global_constraints", []),
        "palette_contract_ref": pkg.get("palette_contract_ref") or c2rgb_path.as_posix(),
        "active_palette_entries": active,
        "metric_transform": transform,
        "image_size": list(Image.open(target_src).size),
        "context_image_size": list(Image.open(context_src).size),
        "target_image_size": list(Image.open(target_src).size),
        "pixels_per_meter": transform.get("pixels_per_meter"),
        "meters_per_pixel": (1.0 / transform["pixels_per_meter"]) if transform.get("pixels_per_meter") else None,
        "prediction_included": bool(pred_raw or pred_quant),
    }
    _write_json(review / "training_record.json", record)

    pred_note = ""
    if not record["prediction_included"]:
        pred_note = "\nPrediction image not included because eval output image was not found.\n"

    md = f"""# One Qwen Training Record Review

sample_id: `{sid}`

metadata_source: `{metadata_path.as_posix()}`

image: `{row['image']}`

context_image: `{row['context_image']}`

## Images

![context](context_image.png)

![target](target_semantic.png)

![side by side](side_by_side_context_target.png)

![target with palette legend](target_with_palette_legend.png)

{pred_note}

## Prompt

```text
{row['prompt']}
```

## Compiled Prompt

```text
{record['compiled_prompt']}
```

## Goal LoState Summary

- required_counts: `{record['required_counts']}`
- pairwise_constraints: `{record['pairwise_constraints']}`
- global_constraints: `{record['global_constraints']}`

## Palette

- palette_contract_ref: `{record['palette_contract_ref']}`
- active_palette_entries: see `palette_entries.json`

## Metric Transform

- image_size: `{record['image_size']}`
- context_image_size: `{record['context_image_size']}`
- target_image_size: `{record['target_image_size']}`
- pixels_per_meter: `{record['pixels_per_meter']}`
- meters_per_pixel: `{record['meters_per_pixel']}`

Full JSON: `training_record.json`
"""
    (review / "training_record.md").write_text(md, encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-base", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional"))
    parser.add_argument("--report-root", type=Path, default=Path("reports/palette_metric_contract_audit"))
    parser.add_argument("--sample-id", default=PREFERRED_SAMPLE_ID)
    parser.add_argument("--c2rgb", type=Path, default=Path("artifacts/semantic_registry_v2/palette_frozen.json"))
    args = parser.parse_args()

    args.report_root.mkdir(parents=True, exist_ok=True)
    quantized_dir = args.output_root / "quantized"
    raw_pred_dir = args.output_root / "infer"

    palette_report = audit_metadata_palette_contract(args.metadata, args.dataset_base, quantized_dir=quantized_dir)
    metric_report = audit_metric_transform_contract(args.metadata, args.dataset_base)
    rule_report = audit_rule_template_prompt_correctness(args.metadata, args.dataset_base)
    record = build_review_package(
        args.dataset_base,
        args.metadata,
        args.output_root,
        args.report_root,
        args.sample_id,
        quantized_dir if quantized_dir.exists() else None,
        raw_pred_dir if raw_pred_dir.exists() else None,
        args.c2rgb,
    )

    _write_json(args.report_root / "palette_contract_audit.json", palette_report)
    _write_json(args.report_root / "metric_transform_audit.json", metric_report)
    _write_json(args.report_root / "rule_template_prompt_correctness_audit.json", rule_report)
    _write_json(args.report_root / "class_color_confusion_matrix.json", palette_report.get("confusion_matrix", {}))
    summary = {
        "palette_contract": palette_report,
        "metric_transform": metric_report,
        "rule_template_prompt": rule_report,
        "sample_training_record": record,
    }
    _write_json(args.report_root / "palette_metric_contract_audit_summary.json", summary)

    (args.report_root / "class_color_confusion_summary.md").write_text(
        "# Class-Color Confusion Summary\n\n"
        f"status: `{palette_report.get('prediction_class_color_confusion_status')}`\n\n"
        f"class_color_pixel_accuracy: `{palette_report.get('class_color_pixel_accuracy')}`\n\n"
        f"furniture_class_color_pixel_accuracy: `{palette_report.get('furniture_class_color_pixel_accuracy')}`\n\n"
        f"most_confused_pairs: `{palette_report.get('most_confused_pairs')}`\n",
        encoding="utf-8",
    )
    print(json.dumps({"report_root": args.report_root.as_posix(), "sample_id": record["sample_id"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
