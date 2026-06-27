import csv
import json

from PIL import Image

from loreflection.qwen_arch_control.prompt_labels.audit_goal_prompt_target_alignment import audit_metadata
from loreflection.semantic_registry import load_registry


def _color(name: str):
    registry = load_registry()
    for category in registry.categories:
        if category.name == name:
            return category.rgb
    raise AssertionError(name)


def test_alignment_audit_rejects_invalid_dropped_relation_in_prompt(tmp_path):
    root = tmp_path / "dataset"
    (root / "cond").mkdir(parents=True)
    (root / "target_full_semantic").mkdir()
    (root / "meta").mkdir()

    Image.new("RGB", (8, 8), _color("floor")).save(root / "cond" / "s_arch_condition.png")
    full = Image.new("RGB", (8, 8), _color("floor"))
    full.putpixel((1, 1), _color("coffee_table"))
    full.putpixel((6, 6), _color("dining_table"))
    full.save(root / "target_full_semantic" / "s_target_full_semantic.png")

    goal = {
        "required_counts": {"coffee_table": 1, "dining_table": 1},
        "pairwise_constraints": [],
        "dropped_pairwise_constraints": [
            {"subject": "coffee_table", "predicate": "near", "object": "dining_table", "prompt_allowed": False}
        ],
    }
    package = {
        "architecture_control_prompt": "Architecture_Control. Follow the architecture condition image.",
        "palette_control_prompt": "Palette_Control. Use the frozen palette.",
        "palette_contract_ref": "configs/c2rgb.json",
        "active_palette_entries": {"coffee_table": [78, 224, 72], "dining_table": [224, 103, 72]},
    }
    (root / "meta" / "s_goal_lostate_geometry_verified.json").write_text(json.dumps(goal), encoding="utf-8")
    (root / "meta" / "s_compiled_prompt_package.json").write_text(json.dumps(package), encoding="utf-8")
    (root / "meta" / "s_relation_alignment_report.json").write_text(
        json.dumps({"full_semantic_report": {"forbidden_architecture_overwrite_rate": 0.0}}),
        encoding="utf-8",
    )
    metadata = root / "metadata.csv"
    with metadata.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image",
                "prompt",
                "context_image",
                "sample_id",
                "goal_lostate",
                "prompt_package",
                "verifier_refs",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "image": "target_full_semantic/s_target_full_semantic.png",
                "prompt": "Context_Control. Keep coffee_table near dining_table. Architecture_Control. Follow the architecture condition image. Palette_Control. Use palette.",
                "context_image": "cond/s_arch_condition.png",
                "sample_id": "s",
                "goal_lostate": "meta/s_goal_lostate_geometry_verified.json",
                "prompt_package": "meta/s_compiled_prompt_package.json",
                "verifier_refs": "meta/s_verifier_refs.json",
            }
        )

    report = audit_metadata(metadata, root)
    assert report["invalid_relation_in_prompt_rate"] == 1.0
    assert report["critical_gates_pass"] is False
