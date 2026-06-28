import csv
from pathlib import Path

from tools.validate_arch_incontext_training_metadata import validate_metadata


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")


def test_arch_incontext_metadata_requires_context_image(tmp_path):
    for rel in [
        "target/sample.png",
        "cond/sample.png",
        "meta/goal.json",
        "meta/prompt.json",
        "meta/verifier.json",
    ]:
        _touch(tmp_path / rel)
    metadata = tmp_path / "metadata.csv"
    with metadata.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "image": "target/sample.png",
                "prompt": "Context_Control. bedroom with bed.",
                "context_image": "cond/sample.png",
                "sample_id": "sample",
                "goal_lostate": "meta/goal.json",
                "prompt_package": "meta/prompt.json",
                "verifier_refs": "meta/verifier.json",
            }
        )
    assert validate_metadata(metadata)["status"] == "pass"


def test_arch_incontext_metadata_rejects_extra_columns(tmp_path):
    metadata = tmp_path / "metadata.csv"
    metadata.write_text(
        "image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs,extra_column\n"
        "a.png,p,c.png,s,g.json,p.json,v.json,unexpected\n",
        encoding="utf-8",
    )
    report = validate_metadata(metadata)
    assert report["status"] == "fail"
    assert "unexpected metadata columns" in " ".join(report["failures"])
