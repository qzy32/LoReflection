#!/usr/bin/env python
"""Build a Prompt Package by calling the runtime Prompt Compiler."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.prompt_builder import compile_prompt_package


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-lostate", required=True, type=Path, help="Input Goal LoState JSON.")
    parser.add_argument("--architecture", required=True, type=Path, help="Input Architecture JSON.")
    parser.add_argument("--architecture-image", default=None, help="Optional architecture condition image.")
    parser.add_argument("--output", required=True, type=Path, help="Output Prompt Package JSON.")
    args = parser.parse_args()
    package = compile_prompt_package(load_json(args.goal_lostate), load_json(args.architecture), args.architecture_image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote Prompt Package to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

