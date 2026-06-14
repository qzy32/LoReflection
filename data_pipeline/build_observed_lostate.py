#!/usr/bin/env python
"""Build Observed LoState by invoking the programmatic observer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.observer import observe


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path, help="Semantic layout image.")
    parser.add_argument("--architecture", required=True, type=Path, help="Architecture JSON.")
    parser.add_argument("--palette", type=Path, default=Path("configs/palette_v1.json"), help="Palette JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output Observed LoState JSON.")
    parser.add_argument("--min-area-px", type=int, default=16, help="Minimum connected component area.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    observed = observe(args.image, load_json(args.architecture), load_json(args.palette), args.output.parent, args.min_area_px)
    args.output.write_text(json.dumps(observed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote Observed LoState to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

