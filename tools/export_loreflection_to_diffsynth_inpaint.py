#!/usr/bin/env python
"""Export LoReflection repair pairs to DiffSynth Qwen-Image inpaint metadata.csv."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from pathlib import Path


COLUMNS = ["image", "blockwise_controlnet_image", "blockwise_controlnet_inpaint_mask", "prompt"]


def load_samples(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("samples", data) if isinstance(data, dict) else data


def resolve(path_text: str, base_dir: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    by_manifest = base_dir / path
    if by_manifest.exists():
        return by_manifest
    return Path.cwd() / path


def materialize(src: Path, dst: Path, mode: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "none":
        return
    if dst.exists():
        return
    if mode == "symlink":
        try:
            os.symlink(src, dst)
            return
        except OSError:
            print(f"[WARN] symlink failed for {src}; falling back to copy.")
    shutil.copy2(src, dst)


def dataset_relative(path: Path, output_dir: Path) -> str:
    return path.relative_to(output_dir).as_posix()


def export(input_path: Path, output_dir: Path, mode: str) -> Path:
    samples = load_samples(input_path)
    base_dir = input_path.parent
    image_dir = output_dir / "images"
    mask_dir = output_dir / "masks"
    rows = []
    for idx, sample in enumerate(samples):
        sample_id = sample.get("sample_id", f"sample_{idx:06d}")
        target_src = resolve(sample["target_image"], base_dir)
        control_src = resolve(sample["control_image"], base_dir)
        mask_src = resolve(sample["control_mask"], base_dir)
        target_dst = image_dir / f"{sample_id}_target{target_src.suffix}"
        control_dst = image_dir / f"{sample_id}_control{control_src.suffix}"
        mask_dst = mask_dir / f"{sample_id}_mask{mask_src.suffix}"
        materialize(target_src, target_dst, mode)
        materialize(control_src, control_dst, mode)
        materialize(mask_src, mask_dst, mode)
        rows.append(
            {
                "image": dataset_relative(target_dst, output_dir),
                "blockwise_controlnet_image": dataset_relative(control_dst, output_dir),
                "blockwise_controlnet_inpaint_mask": dataset_relative(mask_dst, output_dir),
                "prompt": sample["correction_prompt"],
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "metadata.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="controlnet_repair_v1/train.json.")
    parser.add_argument("--output-dir", required=True, type=Path, help="DiffSynth dataset output directory.")
    parser.add_argument("--mode", choices=["copy", "symlink", "none"], default="copy", help="How to materialize image files.")
    args = parser.parse_args()
    csv_path = export(args.input, args.output_dir, args.mode)
    print(f"Wrote DiffSynth metadata to {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
