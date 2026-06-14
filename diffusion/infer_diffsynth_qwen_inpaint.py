#!/usr/bin/env python
"""Placeholder DiffSynth Qwen-Image local inpainting executor."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-image", required=True, type=Path, help="Current semantic layout image.")
    parser.add_argument("--control-mask", required=True, type=Path, help="Binary control mask.")
    parser.add_argument("--prompt", required=True, help="Correction prompt.")
    parser.add_argument("--model-path", default="/server/path/to/Qwen-Image", help="Server model path placeholder.")
    parser.add_argument("--lora-path", default="/server/path/to/loreflection_lora", help="Server LoRA path placeholder.")
    parser.add_argument("--output", required=True, type=Path, help="Output repaired image.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.control_image, args.output)
    print(f"Copied control image to placeholder output {args.output}; no diffusion model was loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
