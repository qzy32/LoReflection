import csv
from pathlib import Path

from loreflection.qwen_arch_control.build_qwen_arch_control_dataset import build_dataset
from tools.validate_arch_incontext_training_metadata import FORBIDDEN_COLUMNS, validate_metadata


def test_metadata_uses_arch_incontext_contract(tmp_path: Path):
    root = tmp_path / "p0"
    build_dataset(root, num_samples=3, image_size=96, seed=11)
    with (root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert {"image", "prompt", "context_image"}.issubset(reader.fieldnames or [])
        assert not (set(reader.fieldnames or []) & FORBIDDEN_COLUMNS)
    assert validate_metadata(root / "metadata.csv", root)["status"] == "pass"
