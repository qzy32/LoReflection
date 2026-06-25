"""Write the current Qwen Architecture In-Context metadata contract."""

from __future__ import annotations

import csv
from pathlib import Path


FIELDNAMES = [
    "image",
    "prompt",
    "context_image",
    "sample_id",
    "goal_lostate",
    "prompt_package",
    "verifier_refs",
]


def write_metadata_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows({key: row[key] for key in FIELDNAMES} for row in rows)
