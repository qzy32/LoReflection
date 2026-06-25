"""Audit condition and target images against the frozen semantic palette."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from PIL import Image

from loreflection.semantic_registry import load_registry


def _colors(path: Path) -> set[tuple[int, int, int]]:
    image = Image.open(path).convert("RGB")
    return {rgb for _, rgb in image.getcolors(maxcolors=image.width * image.height) or []}


def audit_palette(dataset_root: Path) -> dict[str, Any]:
    registry = load_registry()
    frozen = set(registry.name_to_rgb.values())
    condition_unknown: set[tuple[int, int, int]] = set()
    target_unknown: set[tuple[int, int, int]] = set()
    row_count = 0
    with (dataset_root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            row_count += 1
            condition_unknown |= _colors(dataset_root / row["context_image"]) - frozen
            target_unknown |= _colors(dataset_root / row["image"]) - frozen
    report = {
        "num_samples": row_count,
        "condition_palette_unknown_rate": 0.0 if not condition_unknown else 1.0,
        "target_palette_unknown_rate": 0.0 if not target_unknown else 1.0,
        "condition_unknown_colors": [list(rgb) for rgb in sorted(condition_unknown)],
        "target_unknown_colors": [list(rgb) for rgb in sorted(target_unknown)],
        "status": "pass" if not condition_unknown and not target_unknown else "fail",
    }
    output = dataset_root / "audits" / "palette_audit_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    args = parser.parse_args()
    report = audit_palette(args.dataset_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
