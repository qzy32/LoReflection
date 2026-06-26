from scripts.qwen_arch_control.run_until_alignment_passes import large_training_allowed


def test_large_training_gate_blocks_failed_smoke():
    assert not large_training_allowed(
        {"critical_gates_pass": True},
        {
            "smoke_pass": False,
            "palette_unknown_rate_after_quantization": 0.0,
            "architecture_preservation_accuracy": 0.85,
            "furniture_pixel_f1": 0.4,
            "forbidden_architecture_overwrite_rate": 0.01,
        },
    )


def test_large_training_gate_allows_only_all_passed_gates():
    assert large_training_allowed(
        {"critical_gates_pass": True},
        {
            "smoke_pass": True,
            "palette_unknown_rate_after_quantization": 0.0,
            "architecture_preservation_accuracy": 0.96,
            "furniture_pixel_f1": 0.36,
            "forbidden_architecture_overwrite_rate": 0.001,
        },
    )
