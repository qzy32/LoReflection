import csv
from pathlib import Path


def test_full_semantic_metadata_keeps_diffusion_image_as_full_target(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.csv"
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
                "target_furniture_only",
                "target_full_semantic",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "image": "target/sample_target_full_semantic.png",
                "prompt": "Context_Control. Generate a semantic layout.",
                "context_image": "cond/sample_arch_condition.png",
                "sample_id": "sample",
                "goal_lostate": "meta/sample_goal_lostate.json",
                "prompt_package": "meta/sample_prompt_package.json",
                "verifier_refs": "meta/sample_verifier_refs.json",
                "target_furniture_only": "target/sample_target_furniture_only.png",
                "target_full_semantic": "target/sample_target_full_semantic.png",
            }
        )

    row = next(csv.DictReader(metadata.open(encoding="utf-8")))

    assert row["image"] == row["target_full_semantic"]
    assert row["target_furniture_only"]
    assert row["context_image"].endswith("_arch_condition.png")
