import csv
from pathlib import Path

from loreflection.qwen_arch_control.build_qwen_arch_control_dataset import build_dataset
from tools.audit_prompt_geometry_leakage import find_leaks
from llm_prompt_test_client import MockDatasetPromptLLMClient


def test_prompts_are_compiler_generated_and_geometry_safe(tmp_path: Path):
    root = tmp_path / "p0"
    build_dataset(root, num_samples=3, image_size=96, seed=13, llm_client=MockDatasetPromptLLMClient())
    with (root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            assert row["prompt"].startswith("Context_Control.")
            assert not find_leaks(row["prompt"])
