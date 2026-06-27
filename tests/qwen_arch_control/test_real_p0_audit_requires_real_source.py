from pathlib import Path

from loreflection.qwen_arch_control.build_qwen_arch_control_dataset import build_dataset
from llm_prompt_test_client import MockDatasetPromptLLMClient


def test_real_package_requires_real_source(tiny_raw_3dfront_root, tmp_path: Path):
    procedural = build_dataset(
        tmp_path / "procedural",
        num_samples=1,
        image_size=96,
        source_mode="procedural_contract",
        llm_client=MockDatasetPromptLLMClient(),
    )
    assert procedural["training_ready"] is False

    real = build_dataset(
        tmp_path / "real",
        num_samples=1,
        image_size=96,
        source_mode="raw_3dfront",
        data_root=tiny_raw_3dfront_root,
        llm_client=MockDatasetPromptLLMClient(),
    )
    assert real["status"] == "pass"
    assert real["training_ready"] is True
