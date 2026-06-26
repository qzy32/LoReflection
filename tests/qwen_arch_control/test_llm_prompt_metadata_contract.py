import csv
import json
from pathlib import Path

from scripts.qwen_arch_control.generate_llm_prompt_variants import build_metadata


def test_llm_metadata_contract(tmp_path: Path):
    template_root = tmp_path / "template"
    output_root = tmp_path / "llm"
    template_root.mkdir()
    with (template_root / "metadata_template_functional.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"])
        writer.writeheader()
        writer.writerow({"image": "../src/target.png", "prompt": "old", "context_image": "../src/cond.png", "sample_id": "s1", "goal_lostate": "meta/s1_goal.json", "prompt_package": "meta/s1_pkg.json", "verifier_refs": "meta/s1_refs.json"})
    outputs = [{"sample_id": "s1", "parse_ok": True, "prompts": {"prompt_llm_short": "Context_Control. short", "prompt_llm_functional": "Context_Control. functional", "prompt_llm_user_like": "Context_Control. user"}}]
    build_metadata(output_root, template_root, outputs)
    rows = list(csv.DictReader((output_root / "metadata_llm_functional.csv").open("r", encoding="utf-8", newline="")))
    assert list(rows[0].keys()) == ["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"]
    assert rows[0]["prompt"] == "Context_Control. functional"
    package = json.loads((output_root / rows[0]["prompt_package"]).read_text(encoding="utf-8"))
    assert package["schema_version"] == "prompt-package-v2-llm"
