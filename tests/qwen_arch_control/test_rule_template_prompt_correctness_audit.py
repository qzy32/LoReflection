import csv
import json

from loreflection.qwen_arch_control.prompt_labels.audit_rule_template_prompt_correctness import audit_rule_template_prompt_correctness


def test_rule_template_prompt_correctness_flags_color_wording(tmp_path):
    base = tmp_path
    (base / "meta").mkdir()
    (base / "meta/goal.json").write_text(json.dumps({"required_counts": {"desk": 1}}), encoding="utf-8")
    metadata = base / "metadata.csv"
    with metadata.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id", "goal_lostate"])
        writer.writeheader()
        writer.writerow({
            "image": "target.png",
            "prompt": "Context_Control. Create one desk with a specific color palette designated for elderlyroom.",
            "context_image": "cond.png",
            "sample_id": "sample",
            "goal_lostate": "meta/goal.json",
        })
    report = audit_rule_template_prompt_correctness(metadata, base)
    assert report["status"] == "fail"
    assert any(item["issue_type"] == "appearance_style_color_wording_risk" for item in report["failure_examples"])
