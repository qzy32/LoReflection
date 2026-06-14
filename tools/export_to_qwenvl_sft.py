#!/usr/bin/env python
"""Convert a Planner SFT manifest into Qwen-VL image + conversations format."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def load_manifest(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("samples", data) if isinstance(data, dict) else data


def read_optional_json(path: str | None, base_dir: Path) -> object | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        by_manifest = base_dir / p
        p = by_manifest if by_manifest.exists() else Path.cwd() / p
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_input_path(path_text: str, base_dir: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    by_manifest = base_dir / path
    return by_manifest if by_manifest.exists() else Path.cwd() / path


def portable_path(path_text: str, base_dir: Path, path_root: Path) -> str:
    path = resolve_input_path(path_text, base_dir)
    try:
        return os.path.relpath(path.resolve(), path_root.resolve()).replace("\\", "/")
    except ValueError:
        return path.as_posix()


def make_human_message(sample: dict, base_dir: Path) -> str:
    parts = [
        "<image>",
        "[CORRECTION_PLANNING_WITH_MASK_PLAN]",
        "Given the current semantic layout image, Goal LoState, Observed LoState, and LoReview, output a RepairPlan JSON with mask_spec and correction_prompt.",
    ]
    for label, key in [
        ("Goal LoState", "goal_lostate"),
        ("Observed LoState", "observed_lostate"),
        ("LoReview", "loreview"),
    ]:
        payload = read_optional_json(sample.get(key), base_dir)
        if payload is not None:
            parts.append(f"{label}:\n{json.dumps(payload, ensure_ascii=False, indent=2)}")
    if sample.get("instruction"):
        parts.append(f"User instruction: {sample['instruction']}")
    return "\n\n".join(parts)


def convert(input_path: Path, output_path: Path, path_root: Path) -> None:
    samples = load_manifest(input_path)
    base_dir = input_path.parent
    rows = []
    for sample in samples:
        repair = sample.get("repairplan_json") or read_optional_json(sample.get("repairplan"), base_dir)
        rows.append(
            {
                "id": sample.get("sample_id", f"sample_{len(rows):06d}"),
                "image": portable_path(sample["image"], base_dir, path_root),
                "conversations": [
                    {"from": "human", "value": make_human_message(sample, base_dir)},
                    {"from": "gpt", "value": json.dumps(repair, ensure_ascii=False, indent=2)},
                ],
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Planner SFT manifest JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output Qwen-VL SFT JSON.")
    parser.add_argument("--path-root", type=Path, default=Path.cwd(), help="Root used to make image paths portable and relative.")
    args = parser.parse_args()
    convert(args.input, args.output, args.path_root)
    print(f"Wrote Qwen-VL SFT data to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
