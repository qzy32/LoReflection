#!/usr/bin/env python
"""Run the complete local LoReflection smoke test without models, data downloads, or training."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def assert_binary_mask(mask_path: Path, control_image_path: Path) -> None:
    mask = Image.open(mask_path).convert("L")
    control = Image.open(control_image_path)
    values = set(mask.getdata())
    assert_true(mask.size == control.size, f"{mask_path} size {mask.size} != control image size {control.size}")
    assert_true(values.issubset({0, 255}), f"{mask_path} is not binary 0/255: {sorted(values)[:8]}")
    assert_true(255 in values, f"{mask_path} has no editable white region")


def assert_final_state_prompt(prompt: str) -> None:
    command_like = re.compile(r"^\s*(move|delete|remove|fix|insert|replace)\b", re.IGNORECASE)
    assert_true(not command_like.search(prompt), f"correction_prompt is command-like: {prompt}")


def run_smoke(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    examples = REPO_ROOT / "examples" / "toy_samples"
    arch = examples / "architecture_v1.json"
    goal = examples / "goal_lostate_v1.json"
    repairplan = examples / "repairplan_v1.json"

    arch_image = output_dir / "arch_condition.png"
    target_image = output_dir / "target_layout.png"
    bad_image = output_dir / "bad_layout.png"
    perturb_manifest = output_dir / "perturbations.json"
    prompt_package = output_dir / "prompt_package_v1.json"
    observed = output_dir / "observed_lostate_v1.json"
    review = output_dir / "loreview_v1.json"
    bbox_mask = output_dir / "control_mask_bbox.png"
    polygon_mask = output_dir / "control_mask_polygon.png"
    instance_mask = output_dir / "control_mask_instance.png"
    controlnet_manifest = output_dir / "controlnet_repair_v1" / "train.json"
    planner_manifest = output_dir / "planner_sft_manifest.json"
    qwenvl_sft = output_dir / "qwenvl_sft.json"
    diffsynth_dir = output_dir / "diffsynth"

    run([sys.executable, "tools/validate_all.py", "--data-root", str(examples)])
    run([sys.executable, "data_pipeline/render_arch_condition.py", "--architecture", str(arch), "--output", str(arch_image)])
    run([sys.executable, "data_pipeline/render_gt_semantic_layout.py", "--goal-lostate", str(goal), "--output", str(target_image)])
    run([sys.executable, "data_pipeline/generate_perturbations.py", "--input-image", str(target_image), "--output-image", str(bad_image), "--manifest", str(perturb_manifest)])
    run([sys.executable, "data_pipeline/build_prompt_package.py", "--goal-lostate", str(goal), "--architecture", str(arch), "--architecture-image", str(arch_image), "--output", str(prompt_package)])
    run([sys.executable, "data_pipeline/build_observed_lostate.py", "--image", str(bad_image), "--architecture", str(arch), "--output", str(observed)])
    run([sys.executable, "data_pipeline/build_loreview.py", "--goal-lostate", str(goal), "--observed-lostate", str(observed), "--output", str(review)])

    polygon_spec = output_dir / "mask_spec_polygon_v1.json"
    write_json(
        polygon_spec,
        {
            "schema_version": "mask-spec-v1",
            "mask_id": "smoke_polygon",
            "image_size_px": [512, 512],
            "items": [{"type": "polygon", "polygon_px": [[250, 210], [330, 215], [325, 295], [245, 288]], "value": 255}],
        },
    )
    instance_spec = output_dir / "mask_spec_instance_v1.json"
    write_json(
        instance_spec,
        {
            "schema_version": "mask-spec-v1",
            "mask_id": "smoke_instance",
            "image_size_px": [512, 512],
            "items": [{"type": "instance_ref", "instance_ref": "bed_1", "value": 255}],
        },
    )

    run([sys.executable, "runtime/mask_tensor_adapter.py", "--mask-spec", str(examples / "mask_spec_v1.json"), "--control-image", str(bad_image), "--output", str(bbox_mask)])
    run([sys.executable, "runtime/mask_tensor_adapter.py", "--mask-spec", str(polygon_spec), "--control-image", str(bad_image), "--output", str(polygon_mask)])
    run([sys.executable, "runtime/mask_tensor_adapter.py", "--mask-spec", str(instance_spec), "--observed-lostate", str(observed), "--control-image", str(bad_image), "--output", str(instance_mask)])

    run(
        [
            sys.executable,
            "data_pipeline/build_controlnet_repair_pairs.py",
            "--target-image",
            str(target_image),
            "--control-image",
            str(bad_image),
            "--control-mask",
            str(bbox_mask),
            "--repairplan",
            str(repairplan),
            "--output",
            str(controlnet_manifest),
        ]
    )
    run(
        [
            sys.executable,
            "data_pipeline/build_planner_sft_data.py",
            "--image",
            str(bad_image),
            "--goal-lostate",
            str(goal),
            "--observed-lostate",
            str(observed),
            "--loreview",
            str(review),
            "--repairplan",
            str(repairplan),
            "--output",
            str(planner_manifest),
        ]
    )
    run([sys.executable, "tools/export_to_qwenvl_sft.py", "--input", str(planner_manifest), "--output", str(qwenvl_sft), "--path-root", str(REPO_ROOT)])
    run([sys.executable, "tools/export_loreflection_to_diffsynth_inpaint.py", "--input", str(controlnet_manifest), "--output-dir", str(diffsynth_dir), "--mode", "copy"])
    run([sys.executable, "tools/validate_all.py", "--data-root", str(output_dir)])

    prompt = load_json(prompt_package)
    positive = prompt["positive_prompt"]
    negative = prompt["negative_prompt"]
    assert_true("bedroom" in positive, "positive_prompt missing room_type")
    assert_true("bed" in positive and "nightstand" in positive, "positive_prompt missing required objects")
    assert_true("adjacent_to" in positive, "positive_prompt missing required relation")
    assert_true("fixed-palette semantic" in positive, "positive_prompt missing fixed-palette semantic map style")
    assert_true("bed" not in negative and "nightstand" not in negative, "negative_prompt mentions target furniture")
    assert_true(any("door_001" in item for item in prompt["architecture_constraints"]), "architecture_constraints missing door anchor")

    review_payload = load_json(review)
    assert_true(all("recommended_action_type" in issue for issue in review_payload["issues"]), "LoReview issue missing recommended_action_type")
    assert_true({"issue_id", "issue_type", "severity", "target_ref"}.issubset(review_payload["issues"][0]), "LoReview issue is incomplete")

    repair = load_json(repairplan)
    assert_true({"action_type", "target_ref", "protected_refs", "mask_spec", "correction_prompt", "acceptance_criteria"}.issubset(repair), "RepairPlan incomplete")
    assert_final_state_prompt(repair["correction_prompt"])

    assert_binary_mask(bbox_mask, bad_image)
    assert_binary_mask(polygon_mask, bad_image)
    assert_binary_mask(instance_mask, bad_image)

    qwen_rows = json.loads(qwenvl_sft.read_text(encoding="utf-8"))
    assert_true(isinstance(qwen_rows, list) and qwen_rows, "Qwen-VL SFT export is empty")
    first = qwen_rows[0]
    assert_true("image" in first and "conversations" in first, "Qwen-VL row missing image/conversations")
    assert_true(not Path(first["image"]).is_absolute(), "Qwen-VL image path must be relative")
    assert_true("[CORRECTION_PLANNING_WITH_MASK_PLAN]" in first["conversations"][0]["value"], "Qwen-VL human message missing task token")
    json.loads(first["conversations"][1]["value"])

    csv_path = diffsynth_dir / "metadata.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert_true(rows and set(rows[0]) == {"image", "blockwise_controlnet_image", "blockwise_controlnet_inpaint_mask", "prompt"}, "DiffSynth metadata columns mismatch")
    row = rows[0]
    assert_true((diffsynth_dir / row["image"]).exists(), "DiffSynth image target file missing")
    assert_true((diffsynth_dir / row["blockwise_controlnet_image"]).exists(), "DiffSynth control image missing")
    assert_true((diffsynth_dir / row["blockwise_controlnet_inpaint_mask"]).exists(), "DiffSynth control mask missing")
    assert_true(row["prompt"] == repair["correction_prompt"], "DiffSynth prompt does not match correction_prompt")

    print("LoReflection local smoke test passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/local_smoke_test"), help="Directory for generated smoke-test artifacts.")
    args = parser.parse_args()
    run_smoke(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
