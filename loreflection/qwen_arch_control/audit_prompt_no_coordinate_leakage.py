"""Audit P0 metadata prompts for current geometry-leakage rules."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from tools.audit_prompt_geometry_leakage import find_leaks


def audit_prompts(dataset_root: Path) -> dict[str, Any]:
    rows = []
    with (dataset_root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            leaks = find_leaks(row["prompt"])
            rows.append({"sample_id": row["sample_id"], "leaks": leaks})
    failures = [row for row in rows if row["leaks"]]
    report = {
        "num_samples": len(rows),
        "failure_count": len(failures),
        "prompt_coordinate_leakage_rate": len(failures) / max(1, len(rows)),
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }
    output = dataset_root / "audits" / "prompt_leakage_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    args = parser.parse_args()
    report = audit_prompts(args.dataset_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
