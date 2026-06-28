#!/usr/bin/env python
"""Strictly apply pre-generated LLM prompt shards to Qwen metadata.

This tool does not call an LLM. It refuses to write metadata if any shard row
uses fallback or fails validation.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"]
RGB_OLD = "Active semantic category palette entries"
RGB_NEW = "Active semantic category RGB palette entries"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{path}:{i}: JSON decode error: {exc}") from exc
    return rows


def prompt_text(obj: dict[str, Any]) -> str:
    return obj.get("compiled_text_prompt") or obj.get("prompt") or obj.get("prompt_package", {}).get("compiled_text_prompt", "")


def normalize_rgb_label(text: str) -> str:
    return text.replace(RGB_OLD, RGB_NEW)


def fallback_used(package: dict[str, Any]) -> bool:
    text = json.dumps(package, ensure_ascii=False)
    return '"fallback": true' in text or '"fallback_used": true' in text


def package_is_llm(package: dict[str, Any]) -> bool:
    return package.get("prompt_compiler") == "llm_functional" or package.get("prompt_compiler_mode") == "llm_functional"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--shard", type=Path, action="append", required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="write metadata and prompt packages after strict validation passes")
    parser.add_argument("--dry-run", action="store_true", help="validate only; do not write metadata or prompt packages")
    args = parser.parse_args()

    metadata_path = args.dataset_root / "metadata.csv"
    with metadata_path.open("r", encoding="utf-8", newline="") as handle:
        metadata_rows = list(csv.DictReader(handle))
    columns = list(metadata_rows[0].keys()) if metadata_rows else []

    shard_by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids = []
    fallback_ids = []
    missing_rgb_ids = []
    non_llm_ids = []
    validation_failed_ids = []

    for shard in args.shard:
        for obj in load_jsonl(shard):
            sid = obj.get("sample_id") or obj.get("task_id")
            if not sid:
                raise RuntimeError(f"{shard}: row without sample_id")
            if sid in shard_by_id:
                duplicate_ids.append(sid)
            shard_by_id[sid] = obj

    metadata_ids = [row["sample_id"] for row in metadata_rows]
    metadata_id_set = set(metadata_ids)
    shard_id_set = set(shard_by_id)
    missing_sample_ids = sorted(metadata_id_set - shard_id_set)
    extra_shard_sample_ids = sorted(shard_id_set - metadata_id_set)

    for sid, obj in shard_by_id.items():
        package = obj.get("prompt_package") or {}
        prompt = normalize_rgb_label(prompt_text(obj))
        if fallback_used(package):
            fallback_ids.append(sid)
        if RGB_NEW not in prompt:
            missing_rgb_ids.append(sid)
        if not package_is_llm(package):
            non_llm_ids.append(sid)
        report = package.get("validation_report") or package.get("llm_prompt_compiler_report") or {}
        status = report.get("status") or report.get("validation_status")
        if status not in {"pass", "llm_pass"}:
            validation_failed_ids.append(sid)

    can_apply = (
        columns == REQUIRED_COLUMNS
        and len(metadata_rows) == len(shard_by_id)
        and not duplicate_ids
        and not missing_sample_ids
        and not extra_shard_sample_ids
        and not fallback_ids
        and not missing_rgb_ids
        and not non_llm_ids
        and not validation_failed_ids
    )

    summary = {
        "dataset_root": str(args.dataset_root),
        "metadata_rows": len(metadata_rows),
        "metadata_columns": columns,
        "shard_rows": sum(1 for _ in shard_by_id),
        "matched_rows": len(metadata_id_set & shard_id_set),
        "updated_metadata_prompt_rows": 0,
        "updated_prompt_package_files": 0,
        "metadata_prompt_with_rgb_rows": 0,
        "metadata_prompt_with_rgb_rows_after_apply": len(metadata_rows) if can_apply else 0,
        "fallback_false_rows": len(shard_by_id) - len(fallback_ids),
        "duplicate_sample_ids": duplicate_ids[:50],
        "missing_sample_ids": missing_sample_ids[:50],
        "extra_shard_sample_ids": extra_shard_sample_ids[:50],
        "fallback_true_count": len(fallback_ids),
        "fallback_true_rows": len(fallback_ids),
        "fallback_true_sample_ids": fallback_ids[:50],
        "missing_rgb_count": len(missing_rgb_ids),
        "missing_rgb_sample_ids": missing_rgb_ids[:50],
        "non_llm_count": len(non_llm_ids),
        "non_llm_sample_ids": non_llm_ids[:50],
        "validation_failed_count": len(validation_failed_ids),
        "validation_failed_sample_ids": validation_failed_ids[:50],
        "status": "pass" if can_apply else "fail",
        "applied": False,
    }

    if can_apply and args.apply:
        new_rows = []
        updated_packages = 0
        for row in metadata_rows:
            obj = shard_by_id[row["sample_id"]]
            package = obj["prompt_package"]
            package["compiled_text_prompt"] = normalize_rgb_label(package["compiled_text_prompt"])
            package["prompt_compiler"] = "llm_functional"
            package.pop("prompt_compiler_mode", None)
            pkg_path = args.dataset_root / row["prompt_package"]
            pkg_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            updated_packages += 1
            new_row = dict(row)
            new_row["prompt"] = package["compiled_text_prompt"]
            new_rows.append(new_row)
        with metadata_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerows(new_rows)
        summary.update({
            "updated_metadata_prompt_rows": len(new_rows),
            "updated_prompt_package_files": updated_packages,
            "metadata_prompt_with_rgb_rows": sum(1 for row in new_rows if RGB_NEW in row["prompt"]),
            "status": "pass",
            "applied": True,
        })

    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"].startswith("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
