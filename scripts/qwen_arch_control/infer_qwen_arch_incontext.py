#!/usr/bin/env python3
"""Run Qwen-Image Architecture In-Context inference for P0 sanity samples."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any

from PIL import Image


EXPECTED_LORA_FAMILY = "Qwen-Image-In-Context-Control-Union"


def _read_rows(metadata: Path) -> list[dict[str, str]]:
    with metadata.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _room_type(dataset_base: Path, row: dict[str, str]) -> str:
    for key in ("verifier_refs", "goal_lostate", "prompt_package"):
        rel = row.get(key)
        if not rel:
            continue
        obj = _read_json(dataset_base / rel)
        if isinstance(obj, dict):
            rt = obj.get("room_type") or obj.get("target_room_type")
            if rt:
                return str(rt)
            if isinstance(obj.get("sample"), dict) and obj["sample"].get("room_type"):
                return str(obj["sample"]["room_type"])
    return "unknown"


def select_rows(dataset_base: Path, rows: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen_rooms: set[str] = set()
    for row in rows:
        room = _room_type(dataset_base, row)
        if room not in seen_rooms:
            selected.append(row)
            seen_rooms.add(room)
        if len(selected) >= count:
            return selected
    seen_ids = {r.get("sample_id") for r in selected}
    for row in rows:
        if row.get("sample_id") not in seen_ids:
            selected.append(row)
        if len(selected) >= count:
            break
    return selected


def write_blocked(out_dir: Path, reason: str, details: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "INFER_BLOCKED_REPORT.md"
    payload = json.dumps(details, ensure_ascii=False, indent=2)
    report.write_text(
        "# P0 Architecture In-Context Inference Blocked\n\n"
        f"Reason: {reason}\n\n"
        "No generated images were fabricated. Fix the missing API/model/runtime issue and rerun inference.\n\n"
        "```json\n" + payload + "\n```\n",
        encoding="utf-8",
    )
    print(report)


def _load_pipeline(diffsynth_root: Path, lora_path: Path, device: str):
    if str(diffsynth_root) not in sys.path:
        sys.path.insert(0, str(diffsynth_root))
    os.chdir(diffsynth_root)
    import torch  # type: ignore
    from diffsynth.pipelines.qwen_image import ModelConfig, QwenImagePipeline  # type: ignore

    pipe = QwenImagePipeline.from_pretrained(
        torch_dtype=torch.bfloat16,
        device=device,
        model_configs=[
            ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="transformer/diffusion_pytorch_model*.safetensors"),
            ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="text_encoder/model*.safetensors"),
            ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="vae/diffusion_pytorch_model.safetensors"),
        ],
        tokenizer_config=ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="tokenizer/"),
    )
    pipe.load_lora(pipe.dit, str(lora_path))
    return pipe


def run_inference(args: argparse.Namespace) -> dict[str, Any]:
    dataset_base = args.dataset_base.resolve()
    metadata = args.metadata.resolve()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = select_rows(dataset_base, _read_rows(metadata), args.num_samples)

    if not args.lora_path.exists():
        raise FileNotFoundError(f"missing P0 LoRA checkpoint: {args.lora_path}")
    if not args.diffsynth_root.exists():
        raise FileNotFoundError(f"missing DiffSynth root: {args.diffsynth_root}")

    pipe = _load_pipeline(args.diffsynth_root.resolve(), args.lora_path.resolve(), args.device)
    results: list[dict[str, Any]] = []
    negative_prompt = args.negative_prompt
    for idx, row in enumerate(rows):
        sid = str(row["sample_id"])
        prompt = str(row["prompt"])
        if not prompt.startswith("Context_Control."):
            prompt = "Context_Control. " + prompt
        context_path = dataset_base / row["context_image"]
        target_path = dataset_base / row["image"]
        context = Image.open(context_path).convert("RGB")
        target = Image.open(target_path).convert("RGB")
        width, height = context.size
        if args.width:
            width = args.width
        if args.height:
            height = args.height
        if context.size != (width, height):
            context_for_pipe = context.resize((width, height), Image.Resampling.NEAREST)
        else:
            context_for_pipe = context
        image = pipe(
            prompt=prompt,
            seed=args.seed + idx,
            negative_prompt=negative_prompt,
            context_image=context_for_pipe,
            height=height,
            width=width,
            num_inference_steps=args.num_inference_steps,
            cfg_scale=args.cfg_scale,
        )
        raw_path = out_dir / f"{sid}_raw.png"
        cond_path = out_dir / f"{sid}_condition.png"
        target_out_path = out_dir / f"{sid}_target.png"
        prompt_path = out_dir / f"{sid}_prompt.txt"
        meta_path = out_dir / f"{sid}_meta.json"
        image.save(raw_path)
        context.save(cond_path)
        target.save(target_out_path)
        prompt_path.write_text(prompt, encoding="utf-8")
        meta = {
            "sample_id": sid,
            "room_type": _room_type(dataset_base, row),
            "context_image": str(context_path),
            "target_image": str(target_path),
            "raw_output": str(raw_path),
            "lora_checkpoint": str(args.lora_path.resolve()),
            "diffsynth_root": str(args.diffsynth_root.resolve()),
            "seed": args.seed + idx,
            "height": height,
            "width": width,
            "num_inference_steps": args.num_inference_steps,
            "cfg_scale": args.cfg_scale,
            "uses_context_image": True,
            "uses_incontext_union": True,
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(meta)
    report = {
        "status": "pass",
        "num_infer_samples": len(results),
        "lora_checkpoint": str(args.lora_path.resolve()),
        "diffsynth_root": str(args.diffsynth_root.resolve()),
        "results": results,
    }
    (out_dir / "infer_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-base", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--lora-path", type=Path, required=True)
    parser.add_argument("--diffsynth-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--num-samples", type=int, default=10)
    parser.add_argument("--height", type=int, default=256)
    parser.add_argument("--width", type=int, default=256)
    parser.add_argument("--num-inference-steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=4411)
    parser.add_argument("--cfg-scale", type=float, default=4.0)
    parser.add_argument("--negative-prompt", default="low quality, blurry, off-palette colors")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    try:
        run_inference(args)
        return 0
    except Exception as exc:
        details = {
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "lora_path": str(args.lora_path),
            "diffsynth_root": str(args.diffsynth_root),
        }
        write_blocked(args.output_dir, str(exc), details)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
