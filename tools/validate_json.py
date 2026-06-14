#!/usr/bin/env python
"""Validate one JSON file or a directory of JSON files against a JSON Schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from jsonschema import Draft202012Validator


def iter_json_files(path: Path) -> Iterable[Path]:
    """Yield JSON files from a file or directory path."""
    if path.is_file():
        yield path
    else:
        yield from sorted(path.rglob("*.json"))


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(schema_path: Path, input_path: Path) -> int:
    """Return the number of validation failures."""
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    failures = 0
    for json_path in iter_json_files(input_path):
        data = load_json(json_path)
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            failures += 1
            print(f"[FAIL] {json_path}")
            for err in errors:
                loc = ".".join(str(p) for p in err.path) or "<root>"
                print(f"  - {loc}: {err.message}")
        else:
            print(f"[OK] {json_path}")
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, type=Path, help="Path to a JSON Schema file.")
    parser.add_argument("--input", required=True, type=Path, help="JSON file or directory to validate.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    failures = validate(args.schema, args.input)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

