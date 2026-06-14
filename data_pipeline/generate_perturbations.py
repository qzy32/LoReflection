#!/usr/bin/env python
"""Generate toy edit perturbations from a semantic layout image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-image", required=True, type=Path, help="Clean semantic layout image.")
    parser.add_argument("--output-image", required=True, type=Path, help="Perturbed semantic layout image.")
    parser.add_argument("--manifest", required=True, type=Path, help="Perturbation manifest JSON.")
    parser.add_argument("--perturbation-type", default="entity_extra", choices=["entity_extra", "entity_missing"], help="Toy perturbation type.")
    args = parser.parse_args()
    image = Image.open(args.input_image).convert("RGB")
    draw = ImageDraw.Draw(image)
    if args.perturbation_type == "entity_extra":
        draw.rectangle([355, 395, 425, 455], fill="#E45756")
    else:
        draw.rectangle([260, 220, 315, 280], fill="#F4F1E8")
    args.output_image.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output_image)
    manifest = {
        "schema_version": "perturbation-manifest-v1",
        "samples": [
            {
                "sample_id": args.output_image.stem,
                "clean_image": args.input_image.as_posix(),
                "perturbed_image": args.output_image.as_posix(),
                "perturbation_type": args.perturbation_type,
            }
        ],
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote perturbation image to {args.output_image} and manifest to {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
