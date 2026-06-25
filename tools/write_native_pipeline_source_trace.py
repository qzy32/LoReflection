#!/usr/bin/env python
"""Write a concise source trace for the native preprocessing pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TRACE = {
    "report_version": "native_pipeline_source_trace_v1",
    "pipeline_type": "source-level native preprocessing",
    "raw_inputs": [
        "3D-FRONT scene JSON files",
        "3D-FUTURE model_info.json",
        "LoReflection palette and category mapping configs",
    ],
    "outputs": [
        "Architecture JSON",
        "architecture condition image",
        "fixed-palette furniture semantic layout",
        "Observed LoState",
        "conversion reports",
    ],
    "call_chain": [
        {
            "stage": "CLI",
            "module": "tools/build_real_val50_prototype.py",
            "responsibility": "parse arguments and call native package builder",
        },
        {
            "stage": "builder",
            "module": "loreflection.builders.scene_package_builder",
            "responsibility": "coordinate scene selection, parsing, category mapping, geometry, rendering, and reports",
        },
        {
            "stage": "scene parsing",
            "module": "loreflection.data.front3d.scene_parser",
            "responsibility": "raw scene id, furniture list, room children, transform links",
        },
        {
            "stage": "model registry",
            "module": "loreflection.data.front3d.future_registry",
            "responsibility": "3D-FUTURE model_info index",
        },
        {
            "stage": "category mapping",
            "module": "loreflection.data.front3d.category_mapper",
            "responsibility": "canonical action and semantic group policy",
        },
        {
            "stage": "room/furniture geometry",
            "module": "loreflection.data.front3d.room_geometry / furniture_geometry",
            "responsibility": "boundary, derived walls, transforms, footprints",
        },
        {
            "stage": "rendering",
            "module": "loreflection.rendering.topdown",
            "responsibility": "semantic and architecture top-down PNG outputs",
        },
    ],
    "semlayoutdiff_processed_output_dependency": False,
    "output_level_adapter_dependency": False,
    "source_evidence": [
        "preprocess/scripts/pickle_threed_front_dataset.py",
        "preprocess/threed_front/datasets/parse_utils.py",
        "preprocess/scripts/data_processor.py",
        "preprocess/metadata/*.json",
        "preprocess/metadata/*.csv",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(TRACE, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Native pipeline source trace written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
