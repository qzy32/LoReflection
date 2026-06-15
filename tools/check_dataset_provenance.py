#!/usr/bin/env python3
"""Summarize LoReflection dataset provenance reports without touching raw data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-report", type=Path, default=Path("reports/dataset_source_gap_analysis.json"))
    parser.add_argument("--bundle-report", type=Path, default=Path("reports/official_3dfront_bundle_check.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/dataset_provenance_report.json"))
    args = parser.parse_args()

    gap = load_json(args.gap_report)
    bundle = load_json(args.bundle_report)
    classification = gap.get("classification", {})
    recommendation = gap.get("recommendation", {})
    bundle_rec = bundle.get("recommendation", {})
    report = {
        "schema_version": "dataset-provenance-report-v1",
        "source_wording": classification.get("safe_wording", "EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle"),
        "official_like": classification.get("official_like"),
        "editroom_provided": classification.get("editroom_provided"),
        "preprocessed_or_derivative": classification.get("preprocessed_or_derivative"),
        "canonical_raw_bundle_root": bundle_rec.get("canonical_raw_bundle_root"),
        "canonical_front_scene_root": bundle_rec.get("canonical_front_scene_root"),
        "canonical_future_model_root": bundle_rec.get("canonical_future_model_root"),
        "canonical_texture_root": bundle_rec.get("canonical_texture_root"),
        "allowed_for": gap.get("usage_policy", {}).get("allowed_for", []),
        "not_recommended_for": gap.get("usage_policy", {}).get("not_recommended_for", []),
        "required_before_main_experiment": gap.get("usage_policy", {}).get("required_before_main_experiment", []),
        "can_continue_val50_prototype": recommendation.get("can_continue_val50_prototype"),
        "final_experiment_policy": recommendation.get("can_use_for_final_aaai_main_experiment"),
    }
    write_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
