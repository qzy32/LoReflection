from pathlib import Path

import numpy as np
from PIL import Image

from scripts.qwen_arch_control.quantize_qwen_output_palette import quantize_outputs


def test_palette_quantization_writes_frozen_palette_image(tmp_path: Path):
    infer = tmp_path / "infer"
    quant = tmp_path / "quantized"
    infer.mkdir()
    arr = np.array([[[1, 2, 3], [250, 250, 250]]], dtype=np.uint8)
    Image.fromarray(arr).save(infer / "sample_001_raw.png")

    report = quantize_outputs(infer, quant, tmp_path / "report.json")

    assert report["num_images"] == 1
    assert report["unknown_color_rate_after_quantization"] == 0.0
    assert "max_palette_distance" in report
    assert (quant / "sample_001_quantized.png").exists()
