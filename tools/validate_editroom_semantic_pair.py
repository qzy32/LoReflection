#!/usr/bin/env python3
"""Validate generated C11.10 EditRoom semantic pair report rows."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> int:
    summary = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/c11_10_action_conversion_summary.csv")
    ok = True
    with summary.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["status"] == "valid":
                sample_ok = (
                    row["palette_validity"] == "True"
                    and row["mask_binary"] == "True"
                    and row["oracle_composite_equal_target"] == "True"
                    and row["nonmask_equality"] == "True"
                )
                print(row["sample_id"], sample_ok)
                ok = ok and sample_ok
            else:
                print(row["sample_id"], row["status"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
