#!/usr/bin/env python3
"""Create tiny and full metadata subsets for P0 sanity training."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _room_type(dataset_base: Path, sample_id: str) -> str:
    manifest = dataset_base / "meta" / f"{sample_id}_sample_manifest.json"
    if not manifest.exists():
        return "unknown"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return str(data.get("room_type") or "unknown")


def _write(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_subsets(metadata: Path, dataset_base: Path, output_dir: Path, tiny_count: int) -> dict[str, object]:
    with metadata.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    chosen: list[dict[str, str]] = []
    seen_room_types: set[str] = set()
    for row in rows:
        room_type = _room_type(dataset_base, row["sample_id"])
        if room_type not in seen_room_types:
            chosen.append(row)
            seen_room_types.add(room_type)
        if len(chosen) >= tiny_count:
            break
    if len(chosen) < tiny_count:
        chosen_ids = {row["sample_id"] for row in chosen}
        for row in rows:
            if row["sample_id"] in chosen_ids:
                continue
            chosen.append(row)
            if len(chosen) >= tiny_count:
                break

    tiny_path = output_dir / f"p0_tiny_{tiny_count}.csv"
    full_path = output_dir / "p0_50.csv"
    _write(tiny_path, fieldnames, chosen)
    _write(full_path, fieldnames, rows)
    report = {
        "metadata": str(metadata),
        "dataset_base": str(dataset_base),
        "tiny_path": str(tiny_path),
        "p0_50_path": str(full_path),
        "tiny_count": len(chosen),
        "p0_count": len(rows),
        "tiny_sample_ids": [row["sample_id"] for row in chosen],
        "status": "pass" if rows and chosen else "fail",
    }
    (output_dir / "subset_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--dataset-base", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tiny-count", type=int, default=8)
    args = parser.parse_args()
    report = build_subsets(args.metadata, args.dataset_base, args.output_dir, args.tiny_count)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
