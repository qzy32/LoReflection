#!/usr/bin/env python
"""Run a lightweight leakage audit over manifests and JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_FORBIDDEN = ["test", "heldout", "validation_target", "3D-FRONT-private"]


def scan_text(path: Path, forbidden: list[str]) -> list[dict]:
    hits = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lowered = text.lower()
    for token in forbidden:
        if token.lower() in lowered:
            hits.append({"file": str(path), "token": token})
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON file or directory to audit.")
    parser.add_argument("--output", type=Path, default=Path("outputs/leakage_audit.json"), help="Audit report JSON.")
    parser.add_argument("--forbidden-token", action="append", default=[], help="Additional forbidden token.")
    args = parser.parse_args()

    forbidden = DEFAULT_FORBIDDEN + args.forbidden_token
    files = [args.input] if args.input.is_file() else sorted(args.input.rglob("*.json"))
    hits = []
    for path in files:
        hits.extend(scan_text(path, forbidden))
    report = {"input": str(args.input), "num_files": len(files), "num_hits": len(hits), "hits": hits}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote leakage audit report to {args.output}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())

