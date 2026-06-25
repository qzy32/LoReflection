"""Build scene-grouped P0 train/validation/test splits."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def _bucket(group_id: str) -> str:
    value = int(hashlib.sha256(group_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if value < 80 else "val" if value < 90 else "test"


def build_splits(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assigned = []
    for row in rows:
        group_id = str(row.get("house_id") or row.get("scene_id") or row["sample_id"])
        assigned.append(
            {
                "sample_id": row["sample_id"],
                "scene_id": row.get("scene_id", row["sample_id"]),
                "house_id": row.get("house_id", ""),
                "split_group": group_id,
                "split": _bucket(group_id),
            }
        )

    fieldnames = ["sample_id", "scene_id", "house_id", "split_group", "split"]
    for name, subset in [
        ("p0_200.csv", assigned),
        ("train.csv", [row for row in assigned if row["split"] == "train"]),
        ("val.csv", [row for row in assigned if row["split"] == "val"]),
        ("test.csv", [row for row in assigned if row["split"] == "test"]),
    ]:
        with (output_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(subset)

    groups_by_split = {
        split: {row["split_group"] for row in assigned if row["split"] == split}
        for split in ("train", "val", "test")
    }
    overlap = (
        (groups_by_split["train"] & groups_by_split["val"])
        | (groups_by_split["train"] & groups_by_split["test"])
        | (groups_by_split["val"] & groups_by_split["test"])
    )
    report = {
        "num_samples": len(assigned),
        "counts": {split: sum(row["split"] == split for row in assigned) for split in groups_by_split},
        "house_id_missing": all(not row["house_id"] for row in assigned),
        "split_group_key": "scene_id" if all(not row["house_id"] for row in assigned) else "house_id",
        "scene_leakage_groups": sorted(overlap),
        "train_val_test_scene_leakage_rate": len(overlap) / max(1, len({row["split_group"] for row in assigned})),
        "status": "pass" if not overlap else "fail",
    }
    (output_dir.parent / "audits").mkdir(parents=True, exist_ok=True)
    (output_dir.parent / "audits" / "split_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = build_splits(payload["samples"], args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
