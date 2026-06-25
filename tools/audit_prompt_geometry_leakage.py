#!/usr/bin/env python3
"""Audit prompt text for geometry leakage forbidden by the v8 Prompt Compiler."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FORBIDDEN_PATTERNS = [
    r"\bcenter_m\b",
    r"\bsize_m\b",
    r"\borientation_deg\b",
    r"\bbbox\b",
    r"\bfootprint\b",
    r"\bpixel\b",
    r"\bpx\b",
    r"\bcm\b",
    r"\bmeter\b",
    r"\bCSS\b",
    r"\bcoordinate\b",
    r"\bsource_json_path\b"
]
COMPILED = [re.compile(pat, re.IGNORECASE) for pat in FORBIDDEN_PATTERNS]


def find_leaks(text: str) -> list[str]:
    leaks = []
    for pattern, regex in zip(FORBIDDEN_PATTERNS, COMPILED):
        if regex.search(text):
            leaks.append(pattern)
    return leaks


def audit_texts(texts: list[str]) -> dict[str, Any]:
    rows = [{"index": idx, "leaks": find_leaks(text), "text": text} for idx, text in enumerate(texts)]
    failures = [row for row in rows if row["leaks"]]
    return {
        "text_count": len(texts),
        "forbidden_patterns": FORBIDDEN_PATTERNS,
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def _texts_from_json(path: Path, key: str) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        value = data.get(key, "")
        return [str(value)]
    if isinstance(data, list):
        return [str(row.get(key, "")) for row in data if isinstance(row, dict)]
    return [str(data)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", action="append", default=[])
    parser.add_argument("--file", type=Path)
    parser.add_argument("--json-key", default="compiled_text_prompt")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    texts = list(args.text)
    if args.file:
        if args.file.suffix.lower() == ".json":
            texts.extend(_texts_from_json(args.file, args.json_key))
        else:
            texts.append(args.file.read_text(encoding="utf-8"))
    report = audit_texts(texts)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
