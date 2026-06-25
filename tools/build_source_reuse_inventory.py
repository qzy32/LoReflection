#!/usr/bin/env python
"""Build a source-reuse inventory for SemLayoutDiff and threed_front code."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


INVENTORY_ROWS = [
    {
        "source_repo": "SemLayoutDiff",
        "source_file": "preprocess/scripts/pickle_threed_front_dataset.py",
        "class_or_function": "main",
        "purpose": "Raw 3D-FRONT parser entry",
        "input": "3D-FRONT scene directory, 3D-FUTURE model_info, 3D-FUTURE model directory",
        "output": "Pickled parsed scenes",
        "dependencies": "threed_front.datasets.parse_utils.parse_threed_front_scenes_from_dataset",
        "called_by": "SemLayoutDiff preprocessing CLI",
        "calls": "parse_threed_front_scenes_from_dataset",
        "license": "see SemLayoutDiff LICENSE",
        "reusable": "yes",
        "reuse_mode": "reference_only",
        "required_modification": "Use as evidence for source-level parser entry; do not run as black-box output adapter.",
        "reason": "LoReflection should parse raw 3D-FRONT/3D-FUTURE directly.",
        "confidence": "hard source evidence",
    },
    {
        "source_repo": "SemLayoutDiff local threed_front",
        "source_file": "preprocess/threed_front/datasets/parse_utils.py",
        "class_or_function": "parse_threed_front_scenes_from_dataset",
        "purpose": "Parse raw scene JSON and connect furniture/model metadata",
        "input": "3D-FRONT JSON, model_info.json, 3D-FUTURE model root",
        "output": "Parsed room/scene objects",
        "dependencies": "threed_front dataset classes",
        "called_by": "pickle_threed_front_dataset.py",
        "calls": "Room/Furniture/ThreedFuture helpers",
        "license": "see local threed_front/SemLayoutDiff license and file headers",
        "reusable": "yes",
        "reuse_mode": "reimplement_with_attribution",
        "required_modification": "Keep LoReflection schema, actions, and architecture/furniture split.",
        "reason": "Core source-level behavior; current R7 avoids direct copy pending full license review.",
        "confidence": "hard source evidence",
    },
    {
        "source_repo": "SemLayoutDiff",
        "source_file": "preprocess/scripts/data_processor.py",
        "class_or_function": "processed semantic/instance export logic",
        "purpose": "Semantic and instance preprocessing evidence",
        "input": "Parsed/pickled scenes and metadata",
        "output": "label maps, instance annotations, npy/json outputs",
        "dependencies": "metadata label/color files",
        "called_by": "SemLayoutDiff preprocessing",
        "calls": "image/array output helpers",
        "license": "see SemLayoutDiff LICENSE",
        "reusable": "yes",
        "reuse_mode": "reference_only",
        "required_modification": "Use policy evidence only; LoReflection keeps native output schema.",
        "reason": "Useful for category/label/instance policy, not copied into R7.",
        "confidence": "hard source evidence",
    },
    {
        "source_repo": "SemLayoutDiff",
        "source_file": "preprocess/metadata/*.json and *.csv",
        "class_or_function": "label/category/color metadata",
        "purpose": "Class vocabulary, semantic indices, and color evidence",
        "input": "metadata files",
        "output": "category/index/RGB mappings",
        "dependencies": "room-type configs",
        "called_by": "preprocessing/rendering scripts",
        "calls": "n/a",
        "license": "see SemLayoutDiff LICENSE",
        "reusable": "yes",
        "reuse_mode": "reference_only",
        "required_modification": "Adapt to LoReflection palette and action taxonomy.",
        "reason": "Evidence source for policy, not a replacement for LoReflection palette.",
        "confidence": "hard source evidence",
    },
    {
        "source_repo": "LoReflection",
        "source_file": "loreflection/builders/scene_package_builder.py",
        "class_or_function": "build",
        "purpose": "Native raw-data package generation",
        "input": "3D-FRONT scenes, 3D-FUTURE model_info, LoReflection configs",
        "output": "Architecture JSON, architecture condition, semantic layout, Observed LoState, reports",
        "dependencies": "LoReflection modules/configs",
        "called_by": "tools/build_real_val50_prototype.py",
        "calls": "native parser/category/geometry/render helpers",
        "license": "LoReflection project",
        "reusable": "yes",
        "reuse_mode": "native_implementation",
        "required_modification": "Future work can split helper functions into narrower modules.",
        "reason": "Current R7 implementation target.",
        "confidence": "implemented",
    },
]


def detect_license(root: Path) -> dict:
    candidates = []
    for pattern in ["LICENSE*", "COPYING*"]:
        candidates.extend(root.glob(pattern))
        candidates.extend((root / "preprocess").glob(pattern) if (root / "preprocess").exists() else [])
        candidates.extend((root / "preprocess" / "threed_front").glob(pattern) if (root / "preprocess" / "threed_front").exists() else [])
    out = {}
    for path in sorted(set(candidates)):
        try:
            out[str(path)] = path.read_text(encoding="utf-8", errors="ignore")[:2000]
        except OSError:
            out[str(path)] = "<unreadable>"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(INVENTORY_ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(INVENTORY_ROWS)

    payload = {
        "report_version": "semlayoutdiff_reusable_source_inventory_v1",
        "source_root": str(args.semlayoutdiff_root),
        "license_candidates": detect_license(args.semlayoutdiff_root),
        "rows": INVENTORY_ROWS,
        "copy_and_modify_performed_in_r7": False,
        "policy": "R7 uses source-level native reimplementation/reference; no third-party function body is copied into LoReflection in this step.",
    }
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Source reuse inventory written to {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
