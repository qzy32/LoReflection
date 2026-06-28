import csv
from pathlib import Path

from loreflection.qwen_arch_control.build_qwen_arch_control_dataset import build_dataset
from tools.validate_arch_incontext_training_metadata import REQUIRED_COLUMNS, validate_metadata
from llm_prompt_test_client import MockDatasetPromptLLMClient


def test_metadata_uses_arch_incontext_contract(tmp_path: Path):
    root = tmp_path / "p0"
    build_dataset(root, num_samples=3, image_size=96, seed=11, llm_client=MockDatasetPromptLLMClient())
    with (root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == REQUIRED_COLUMNS
    assert validate_metadata(root / "metadata.csv", root)["status"] == "pass"
