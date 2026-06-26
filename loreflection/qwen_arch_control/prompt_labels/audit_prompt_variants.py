from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from tools.audit_prompt_geometry_leakage import find_leaks


def audit_prompt_label_dataset(dataset_root: Path, output: Path | None = None) -> dict[str, Any]:
    variant_files = sorted(dataset_root.glob("metadata_template_*.csv"))
    rows = []
    for path in variant_files:
        with path.open("r", encoding="utf-8", newline="") as f:
            rows.extend({**row, "variant_file": path.name} for row in csv.DictReader(f))
    sample_ids = sorted({row["sample_id"] for row in rows})
    starts = [row["prompt"].startswith("Context_Control.") for row in rows]
    leaks = [bool(find_leaks(row["prompt"])) for row in rows]
    coverage = []
    unknown_terms = []
    for row in rows:
        goal_path = dataset_root / row["goal_lostate"]
        goal = json.loads(goal_path.read_text(encoding="utf-8"))
        cats = [slot["category"] for slot in goal.get("furniture_slots", [])]
        text = row["prompt"].replace("_", " ")
        coverage.append(all(cat.replace("_", " ") in text for cat in cats))
        unknown_terms.append("unknown" in text.lower())
    per_sample = {sid: 0 for sid in sample_ids}
    for row in rows:
        per_sample[row["sample_id"]] += 1
    report = {
        "num_samples": len(sample_ids),
        "variant_count_per_sample": min(per_sample.values()) if per_sample else 0,
        "starts_with_context_control_rate": sum(starts) / max(1, len(starts)),
        "coordinate_leakage_rate": sum(leaks) / max(1, len(leaks)),
        "required_slot_coverage_rate": sum(coverage) / max(1, len(coverage)),
        "unknown_category_term_rate": sum(unknown_terms) / max(1, len(unknown_terms)),
        "template_variant_rate": 1.0 if variant_files else 0.0,
        "llm_request_exported": (Path("data/loreflection_prompt_label_requests/p1_small_metric_v2_prompt_label_requests.jsonl")).exists(),
        "llm_actual_generation_used": False,
    }
    report["status"] = "pass" if report["num_samples"] == 200 and report["variant_count_per_sample"] >= 3 and report["starts_with_context_control_rate"] == 1.0 and report["coordinate_leakage_rate"] == 0.0 and report["required_slot_coverage_rate"] == 1.0 and report["unknown_category_term_rate"] == 0.0 else "fail"
    output = output or dataset_root / "audits" / "prompt_variant_audit_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
