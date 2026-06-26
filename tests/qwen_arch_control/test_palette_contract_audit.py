import csv
import json

from loreflection.qwen_arch_control.prompt_labels.audit_palette_contract import audit_metadata_palette_contract


def test_palette_contract_audit_reports_compiled_prompt_controls(tmp_path):
    base = tmp_path
    (base / "meta").mkdir()
    goal = base / "meta/sample_goal.json"
    goal.write_text(json.dumps({"required_counts": {"desk": 1}}), encoding="utf-8")
    pkg = base / "meta/sample_pkg.json"
    pkg.write_text(
        json.dumps({"palette_contract_ref": "palette.json", "active_palette_entries": {"desk": [1, 2, 3]}}),
        encoding="utf-8",
    )
    metadata = base / "metadata.csv"
    with metadata.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"])
        writer.writeheader()
        writer.writerow({
            "image": "target.png",
            "prompt": "Context_Control. x\n\nArchitecture_Control. y\n\nPalette_Control. z",
            "context_image": "cond.png",
            "sample_id": "sample",
            "goal_lostate": "meta/sample_goal.json",
            "prompt_package": "meta/sample_pkg.json",
            "verifier_refs": "meta/verifier.json",
        })
    report = audit_metadata_palette_contract(metadata, base)
    assert report["compiled_prompt_has_palette_control_rate"] == 1.0
    assert report["active_palette_entries_cover_required_categories_rate"] == 1.0
