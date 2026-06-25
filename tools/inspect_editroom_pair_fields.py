#!/usr/bin/env python3
"""Inspect C11.10 real EditRoom pair audit output."""

from pathlib import Path


def main() -> None:
    path = Path("reports/c11_10_editroom_pair_audit.json")
    print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
