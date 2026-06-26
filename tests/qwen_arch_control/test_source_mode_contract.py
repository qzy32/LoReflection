from pathlib import Path

from loreflection.qwen_arch_control.build_qwen_arch_control_dataset import build_dataset


def test_procedural_contract_is_never_training_ready(tmp_path: Path):
    result = build_dataset(
        tmp_path / "procedural",
        num_samples=2,
        image_size=96,
        source_mode="procedural_contract",
    )
    assert result["status"] == "contract_pass"
    assert result["training_ready"] is False
