import json

import numpy as np
from PIL import Image

from loreflection.qwen_arch_control.metric_transform import build_metric_transform
from loreflection.qwen_arch_control.parse_qwen_semantic_output_metric import parse_output
from loreflection.semantic_registry import load_registry


def test_metric_parser_uses_explicit_metric_transform(tmp_path):
    registry = load_registry()
    sid = sorted(registry.object_ids)[0]
    rgb = registry.id_to_rgb[sid]
    arr = np.zeros((32, 32, 3), dtype=np.uint8)
    arr[10:14, 10:15] = rgb
    image = tmp_path / "sample_quantized.png"
    Image.fromarray(arr).save(image)
    boundary = [[0, 0], [4, 0], [4, 4], [0, 4]]
    arch = tmp_path / "arch.json"
    arch.write_text(json.dumps({"boundary": {"polygon_m": boundary}, "metric_transform": build_metric_transform(boundary, image_size_px=32, canvas_extent_m=4.0)}), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"sample_id": "sample"}), encoding="utf-8")
    result = parse_output(image, arch, manifest, min_area=2)
    assert result["source"]["parse_transform_mode"] == "metric_transform"
    assert result["objects"]
    assert result["objects"][0]["parse_transform_mode"] == "metric_transform"
