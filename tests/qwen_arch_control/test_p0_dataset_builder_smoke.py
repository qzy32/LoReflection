from pathlib import Path

from loreflection.qwen_arch_control.build_qwen_arch_control_dataset import build_dataset
from llm_prompt_test_client import MockDatasetPromptLLMClient


def test_builder_creates_tiny_contract_package(tmp_path: Path):
    root = tmp_path / "p0"
    result = build_dataset(root, num_samples=4, image_size=128, seed=7, llm_client=MockDatasetPromptLLMClient())
    assert result["status"] == "contract_pass"
    assert result["training_ready"] is False
    assert (root / "metadata.csv").exists()
    assert len(list((root / "cond").glob("*.png"))) == 4
    assert len(list((root / "target").glob("*.png"))) == 4
