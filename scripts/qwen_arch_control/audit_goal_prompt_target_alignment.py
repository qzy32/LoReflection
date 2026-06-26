#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loreflection.qwen_arch_control.prompt_labels.audit_goal_prompt_target_alignment import audit_metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--dataset-base", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    report = audit_metadata(args.metadata, args.dataset_base)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Goal-Prompt-Target Alignment Audit",
        "",
        f"- critical_gates_pass: `{report['critical_gates_pass']}`",
        f"- required_category_coverage_rate: `{report['required_category_coverage_rate']}`",
        f"- required_count_coverage_rate: `{report['required_count_coverage_rate']}`",
        f"- geometry_verified_prompt_relation_rate: `{report['geometry_verified_prompt_relation_rate']}`",
        f"- invalid_relation_in_prompt_rate: `{report['invalid_relation_in_prompt_rate']}`",
        f"- compiled_prompt_has_architecture_control_rate: `{report['compiled_prompt_has_architecture_control_rate']}`",
        f"- compiled_prompt_has_palette_control_rate: `{report['compiled_prompt_has_palette_control_rate']}`",
        f"- palette_contract_ref_exists_rate: `{report['palette_contract_ref_exists_rate']}`",
        f"- active_palette_entries_cover_required_categories_rate: `{report['active_palette_entries_cover_required_categories_rate']}`",
        f"- target_full_semantic_contains_architecture_rate: `{report['target_full_semantic_contains_architecture_rate']}`",
        f"- target_full_semantic_contains_required_furniture_rate: `{report['target_full_semantic_contains_required_furniture_rate']}`",
        f"- forbidden_architecture_overwrite_rate: `{report['forbidden_architecture_overwrite_rate']}`",
        f"- coordinate_leakage_rate: `{report['coordinate_leakage_rate']}`",
        f"- old_route_fields_present: `{report['old_route_fields_present']}`",
        f"- metric_transform_exists_rate: `{report['metric_transform_exists_rate']}`",
        f"- same_resolution_rate: `{report['same_resolution_rate']}`",
        f"- context_and_target_share_transform: `{report['context_and_target_share_transform']}`",
        "",
        "## Failure Samples",
        "",
    ]
    for failure in report.get("failures", [])[:50]:
        lines.append(f"- `{failure.get('sample_id')}` `{failure.get('issue_type')}` status={failure.get('status')}")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
