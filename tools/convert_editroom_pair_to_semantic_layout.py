#!/usr/bin/env python3
"""Entry point note for C11.10 real EditRoom semantic conversion.

The C11.10 conversion ran on A800 against real EditRoom pickle pairs. The
durable artifacts are mirrored locally under:

- reports/c11_10_*.json
- outputs/manual_review/c11_10_editroom_semantic_conversion.zip

Rerun `python scripts/run_c11_10_remote.py` from this workstation to regenerate
the server-side outputs.
"""

from pathlib import Path


def main() -> None:
    print("C11.10 reports:", Path("reports").resolve())
    print("C11.10 review zip:", Path("outputs/manual_review/c11_10_editroom_semantic_conversion.zip").resolve())


if __name__ == "__main__":
    main()
