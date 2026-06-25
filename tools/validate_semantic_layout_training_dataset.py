#!/usr/bin/env python3
"""Validate the semantic layout overfit dataset structure."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = [
    "architecture_label_map.npy",
    "architecture_condition_rgb.png",
    "control_mask.png",
    "furniture_label_map.npy",
    "furniture_semantic_rgb.png",
    "target_composite_label_map.npy",
    "target_composite_rgb.png",
    "instance_id_map.npy",
    "instance_annotations.json",
    "prompt.json",
    "coordinate_transform.json",
    "apm_supervision.json",
    "sample_manifest.json",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=Path("/wuqingyaoa800/qiuziyan/loreflection_outputs/semantic_layout_38class_overfit32_clean_v1"))
    parser.add_argument("--output", type=Path, default=Path("reports/overfit32_dataset_validation.json"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    manifest_path = args.dataset_root / "dataset_manifest.json"
    failures = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    if not manifest:
        failures.append("missing dataset_manifest.json")
    for sample in manifest.get("samples", []):
        sd = args.dataset_root / "samples" / sample["sample_id"]
        for name in REQUIRED:
            if not (sd / name).exists():
                failures.append(f"{sample['sample_id']}: missing {name}")
        prompt = json.loads((sd / "prompt.json").read_text(encoding="utf-8")) if (sd / "prompt.json").exists() else {}
        if any(k in json.dumps(prompt).lower() for k in ["yaw", "rotation", "facing", "asset id"]):
            failures.append(f"{sample['sample_id']}: prompt contains orientation/asset term")
    report = {"dataset_root": str(args.dataset_root), "sample_count": manifest.get("sample_count", 0), "failures": failures, "strict_validation": not failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
