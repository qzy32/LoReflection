"""Build a bounded Qwen Architecture In-Context P0 contract dataset."""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from loreflection.goal.prompt_compiler import compile_prompt_package
from loreflection.qwen_arch_control.audit_palette_exact import audit_palette
from loreflection.qwen_arch_control.audit_prompt_no_coordinate_leakage import audit_prompts
from loreflection.qwen_arch_control.audit_qwen_arch_control_dataset import audit_dataset
from loreflection.qwen_arch_control.build_splits import build_splits
from loreflection.qwen_arch_control.goal_label_extractor_from_layout import extract_goal_lostate
from loreflection.qwen_arch_control.preview_qwen_arch_dataset import build_preview
from loreflection.qwen_arch_control.raw_3dfront_adapter import adapt_scene_file
from loreflection.qwen_arch_control.render_architecture_condition import render_architecture_condition
from loreflection.qwen_arch_control.render_target_semantic_layout import render_target_semantic_layout
from loreflection.qwen_arch_control.source_resolver import (
    iter_raw_scene_records,
    load_model_info_index,
    probe_data_root,
)
from loreflection.qwen_arch_control.write_metadata_csv import write_metadata_csv
from loreflection.semantic_registry import load_registry
from tools.validate_arch_incontext_training_metadata import validate_metadata


ROOT = Path(__file__).resolve().parents[2]
GOAL_SCHEMA = ROOT / "artifacts" / "current_interface" / "goal_lostate.schema.json"
ROOM_TEMPLATES = {
    "bedroom": ["double_bed", "nightstand", "wardrobe", "desk", "chair"],
    "livingroom": ["sofa", "coffee_table", "tv_stand", "armchair", "cabinet"],
    "diningroom": ["dining_table", "dining_chair", "cabinet", "pendant_lamp"],
    "study": ["desk", "chair", "bookshelf", "cabinet", "lounge_chair"],
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _box(index: int, image_size: int, rng: random.Random) -> list[int]:
    margin = max(12, image_size // 16)
    usable = image_size - 2 * margin
    cols = 3
    cell_w = usable // cols
    cell_h = usable // 3
    col, row = index % cols, (index // cols) % 3
    x0 = margin + col * cell_w + rng.randint(3, max(4, cell_w // 8))
    y0 = margin + row * cell_h + rng.randint(3, max(4, cell_h // 8))
    width = rng.randint(max(12, cell_w // 3), max(14, cell_w - 10))
    height = rng.randint(max(12, cell_h // 3), max(14, cell_h - 10))
    return [x0, y0, min(image_size - margin, x0 + width), min(image_size - margin, y0 + height)]


def _procedural_source(sample_index: int, image_size: int, seed: int) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(seed + sample_index * 7919)
    room_type = list(ROOM_TEMPLATES)[sample_index % len(ROOM_TEMPLATES)]
    sample_id = f"p0_scene_{sample_index:04d}"
    base_margin = max(12, image_size // 16)
    left = base_margin + rng.randint(0, image_size // 14)
    right = image_size - base_margin - rng.randint(0, image_size // 14)
    top = base_margin + rng.randint(0, image_size // 18)
    bottom = image_size - base_margin - rng.randint(0, image_size // 18)
    door_center = rng.randint(left + 24, right - 24)
    window_center = rng.randint(left + 30, right - 30)
    window_half_width = rng.randint(20, 38)
    architecture = {
        "schema_version": "architecture-v2-p0",
        "architecture_id": sample_id,
        "scene_id": sample_id,
        "room_type": room_type,
        "image_size_px": [image_size, image_size],
        "boundary": {
            "polygon_px": [
                [left, top],
                [right, top],
                [right, bottom],
                [left, bottom],
            ]
        },
        "anchors": [
            {
                "anchor_id": f"{sample_id}:door",
                "anchor_type": "door",
                "bbox_px": [door_center - 16, bottom - 4, door_center + 16, bottom + 4],
            },
            {
                "anchor_id": f"{sample_id}:window",
                "anchor_type": "window",
                "bbox_px": [window_center - window_half_width, top - 4, window_center + window_half_width, top + 4],
            },
            {
                "anchor_id": f"{sample_id}:door_clearance",
                "anchor_type": "clearance",
                "polygon_px": [
                    [door_center - 24, bottom - 40],
                    [door_center + 24, bottom - 40],
                    [door_center + 24, bottom],
                    [door_center - 24, bottom],
                ],
            },
        ],
        "source": {"kind": "procedural_contract", "seed": seed + sample_index * 7919},
    }
    categories = ROOM_TEMPLATES[room_type]
    object_count = 3 + sample_index % 3
    objects = [
        {
            "instance_id": f"{sample_id}:{category}_{idx:02d}",
            "category": category,
            "bbox_px": _box(idx, image_size, rng),
        }
        for idx, category in enumerate(categories[:object_count])
    ]
    if room_type == "diningroom":
        objects.append(
            {
                "instance_id": f"{sample_id}:dining_chair_extra",
                "category": "dining_chair",
                "bbox_px": _box(len(objects), image_size, rng),
            }
        )
    layout = {
        "schema_version": "layout-json-v1",
        "layout_id": f"{sample_id}_layout",
        "sample_id": sample_id,
        "scene_id": sample_id,
        "room_type": room_type,
        "image_size_px": [image_size, image_size],
        "objects": objects,
        "source": {"kind": "procedural_contract"},
    }
    return architecture, layout


def _procedural_records(num_samples: int, image_size: int, seed: int) -> list[dict[str, Any]]:
    records = []
    for index in range(num_samples):
        architecture, layout = _procedural_source(index, image_size, seed)
        records.append(
            {
                "sample_id": architecture["architecture_id"],
                "scene_id": architecture["scene_id"],
                "house_id": None,
                "floorplan_id": architecture["scene_id"],
                "room_type": architecture["room_type"],
                "source_scene_json": None,
                "architecture": architecture,
                "layout": layout,
                "warnings": [
                    "procedural_contract is only for interface smoke test, not real training data",
                    "wall represented by palette-exact floor/void boundary because frozen registry has no wall category",
                ],
                "skipped_objects": [],
            }
        )
    return records


def _raw_records(data_root: Path, num_samples: int, image_size: int, seed: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    probe = probe_data_root(data_root)
    model_paths = [Path(path) for path in probe["model_info_paths"]]
    model_index = load_model_info_index(model_paths)
    records = []
    skip_reasons: dict[str, int] = {}
    scanned_scenes = 0
    for source in iter_raw_scene_records(data_root, seed):
        scanned_scenes += 1
        try:
            rooms = adapt_scene_file(Path(source["source_scene_json"]), model_index, image_size)
        except Exception as exc:
            key = f"adapter_error:{type(exc).__name__}"
            skip_reasons[key] = skip_reasons.get(key, 0) + 1
            continue
        if not rooms:
            skip_reasons["no_room_with_two_mapped_objects"] = skip_reasons.get("no_room_with_two_mapped_objects", 0) + 1
            continue
        for room in rooms:
            records.append(room)
            if len(records) >= num_samples:
                break
        if len(records) >= num_samples:
            break
    if len(records) < num_samples:
        raise RuntimeError(
            f"Only {len(records)} raw 3D-FRONT room samples were constructed after scanning {scanned_scenes} scenes"
        )
    return records, {
        "probe": probe,
        "model_info_entry_count": len(model_index),
        "scanned_scene_count": scanned_scenes,
        "skip_reasons": skip_reasons,
    }


def _scene_package_records(scene_package_root: Path, num_samples: int) -> list[dict[str, Any]]:
    manifest_path = scene_package_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = []
    for sample in manifest.get("samples", []):
        architecture_path = scene_package_root / str(sample.get("architecture_json", ""))
        layout_path = scene_package_root / str(sample.get("layout_json", ""))
        if not architecture_path.exists() or not layout_path.exists():
            continue
        architecture = json.loads(architecture_path.read_text(encoding="utf-8"))
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        if len(layout.get("objects", [])) < 2:
            continue
        records.append(
            {
                "sample_id": layout["sample_id"],
                "scene_id": layout.get("scene_id", layout["sample_id"]),
                "house_id": layout.get("house_id"),
                "floorplan_id": layout.get("floorplan_id"),
                "room_type": layout.get("room_type"),
                "source_scene_json": layout.get("source", {}).get("source_scene_json"),
                "architecture": architecture,
                "layout": layout,
                "warnings": sample.get("warnings", []),
                "skipped_objects": layout.get("skipped_objects", []),
            }
        )
        if len(records) >= num_samples:
            break
    if len(records) < num_samples:
        raise RuntimeError(f"Scene package yielded {len(records)} usable samples; requested {num_samples}")
    return records


def build_dataset(
    output_root: Path,
    num_samples: int = 60,
    image_size: int = 256,
    seed: int = 4411,
    clean: bool = True,
    source_mode: str = "procedural_contract",
    data_root: Path | None = None,
    scene_package_root: Path | None = None,
) -> dict[str, Any]:
    if not 1 <= num_samples <= 200:
        raise ValueError("P0 num_samples must be between 1 and 200")
    if clean and output_root.exists():
        shutil.rmtree(output_root)
    for name in ("cond", "target", "meta", "audits", "splits", "previews"):
        (output_root / name).mkdir(parents=True, exist_ok=True)

    registry = load_registry()
    goal_validator = Draft202012Validator(json.loads(GOAL_SCHEMA.read_text(encoding="utf-8")))
    metadata_rows = []
    samples = []
    source_details: dict[str, Any] = {}
    if source_mode == "procedural_contract":
        records = _procedural_records(num_samples, image_size, seed)
    elif source_mode == "raw_3dfront":
        if data_root is None:
            raise ValueError("--data-root is required for raw_3dfront")
        records, source_details = _raw_records(data_root, num_samples, image_size, seed)
    elif source_mode == "real_scene_package":
        if scene_package_root is None:
            raise ValueError("--scene-package-root is required for real_scene_package")
        records = _scene_package_records(scene_package_root, num_samples)
    else:
        raise ValueError(f"Unsupported source_mode: {source_mode}")

    for record in records:
        architecture = record["architecture"]
        layout = record["layout"]
        sample_id = record["sample_id"]
        goal = extract_goal_lostate(layout, architecture, registry)
        errors = list(goal_validator.iter_errors(goal))
        if errors:
            raise ValueError(f"{sample_id} Goal LoState schema failure: {errors[0].message}")
        prompt_package = compile_prompt_package(goal)
        verifier_refs = {
            "sample_id": sample_id,
            "architecture_ref": architecture["architecture_id"],
            "constraint_refs": [c["constraint_id"] for c in goal["goal_constraints"]],
            "required_slot_refs": [slot["slot_id"] for slot in goal["furniture_slots"]],
        }

        paths = {
            "condition": Path("cond") / f"{sample_id}_arch_condition.png",
            "target": Path("target") / f"{sample_id}_target_semantic.png",
            "architecture": Path("meta") / f"{sample_id}_architecture.json",
            "layout": Path("meta") / f"{sample_id}_layout.json",
            "goal": Path("meta") / f"{sample_id}_goal_lostate.json",
            "prompt": Path("meta") / f"{sample_id}_prompt_package.json",
            "verifier": Path("meta") / f"{sample_id}_verifier_refs.json",
            "manifest": Path("meta") / f"{sample_id}_sample_manifest.json",
        }
        condition_report = render_architecture_condition(
            architecture, output_root / paths["condition"], image_size, registry
        )
        target_report = render_target_semantic_layout(
            layout, output_root / paths["target"], image_size, registry
        )
        _write_json(output_root / paths["architecture"], architecture)
        _write_json(output_root / paths["layout"], layout)
        _write_json(output_root / paths["goal"], goal)
        _write_json(output_root / paths["prompt"], prompt_package)
        _write_json(output_root / paths["verifier"], verifier_refs)
        sample_manifest = {
            "sample_id": sample_id,
            "scene_id": record["scene_id"],
            "house_id": record.get("house_id"),
            "floorplan_id": record.get("floorplan_id"),
            "source_mode": source_mode,
            "source_kind": architecture["source"]["kind"],
            "source_scene_json": record.get("source_scene_json"),
            "paths": {key: path.as_posix() for key, path in paths.items() if key != "manifest"},
            "condition_contract": condition_report,
            "target_contract": target_report,
            "warnings": record.get("warnings", []),
            "skipped_objects": record.get("skipped_objects", []),
        }
        _write_json(output_root / paths["manifest"], sample_manifest)
        metadata_rows.append(
            {
                "image": paths["target"].as_posix(),
                "prompt": prompt_package["compiled_text_prompt"],
                "context_image": paths["condition"].as_posix(),
                "sample_id": sample_id,
                "goal_lostate": paths["goal"].as_posix(),
                "prompt_package": paths["prompt"].as_posix(),
                "verifier_refs": paths["verifier"].as_posix(),
            }
        )
        samples.append(
            {
                "sample_id": sample_id,
                "scene_id": record["scene_id"],
                "house_id": record.get("house_id"),
                "floorplan_id": record.get("floorplan_id"),
                "source_kind": architecture["source"]["kind"],
            }
        )

    write_metadata_csv(output_root / "metadata.csv", metadata_rows)
    package_manifest = {
        "schema_version": "qwen-arch-control-p0-v1",
        "num_samples": len(samples),
        "source_mode": source_mode,
        "training_ready": source_mode in {"raw_3dfront", "real_scene_package"},
        "image_contract": {
            "image": "furniture-only target_semantic_layout_image",
            "context_image": "architecture-only architecture_condition_image",
            "prompt": "Prompt Compiler compiled_text_prompt",
        },
        "source_policy": (
            "procedural_contract is only for interface smoke test, not real training data"
            if source_mode == "procedural_contract"
            else "real source package suitable for bounded sanity training after all audits pass"
        ),
        "source_details": source_details,
        "samples": samples,
    }
    _write_json(output_root / "meta" / "p0_dataset_manifest.json", package_manifest)
    split_report = build_splits(samples, output_root / "splits")
    metadata_report = validate_metadata(output_root / "metadata.csv", output_root)
    _write_json(output_root / "audits" / "metadata_validator_report.json", metadata_report)
    palette_report = audit_palette(output_root)
    prompt_report = audit_prompts(output_root)
    dataset_report = audit_dataset(output_root)
    preview_report = build_preview(output_root)
    result = {
        "dataset_root": str(output_root),
        "num_samples": num_samples,
        "source_mode": source_mode,
        "training_ready": bool(dataset_report.get("training_ready")),
        "metadata_validator": metadata_report["status"],
        "split_audit": split_report["status"],
        "palette_audit": palette_report["status"],
        "prompt_audit": prompt_report["status"],
        "dataset_audit": dataset_report["status"],
        "preview": preview_report,
        "status": ("contract_pass" if source_mode == "procedural_contract" else "pass")
        if all(
            report["status"] in {"pass", "contract_pass"}
            for report in (metadata_report, split_report, palette_report, prompt_report, dataset_report)
        )
        else "fail",
    }
    _write_json(output_root / "audits" / "p0_build_result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-mode",
        choices=["procedural_contract", "real_scene_package", "raw_3dfront"],
        default="raw_3dfront",
    )
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--scene-package-root", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("data/loreflection_qwen_arch_control_real_p0"))
    parser.add_argument("--num-samples", type=int, default=60)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--seed", type=int, default=4411)
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()
    result = build_dataset(
        args.output_root,
        args.num_samples,
        args.image_size,
        args.seed,
        not args.no_clean,
        args.source_mode,
        args.data_root,
        args.scene_package_root,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"pass", "contract_pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
