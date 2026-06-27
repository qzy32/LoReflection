import json
from pathlib import Path

import numpy as np
from PIL import Image

from loreflection.qwen_arch_control.parse_qwen_semantic_output_metric import parse_output
from loreflection.semantic_registry import load_registry


def test_parser_ignores_architecture_colors_and_parses_furniture(tmp_path: Path):
    registry = load_registry()
    furniture_id = sorted(registry.object_ids)[0]
    furniture_rgb = registry.id_to_rgb[furniture_id]
    category = registry.id_to_name[furniture_id]
    arr = np.zeros((16, 16, 3), dtype=np.uint8)
    arr[:, :] = registry.name_to_rgb.get("floor", (0, 0, 0))
    arr[4:8, 5:10] = furniture_rgb
    image = tmp_path / "sample_quantized.png"
    Image.fromarray(arr).save(image)
    arch = tmp_path / "sample_architecture.json"
    arch.write_text(json.dumps({"boundary": {"polygon_m": [[0, 0], [4, 0], [4, 4], [0, 4]], "polygon_px": [[0, 0], [16, 0], [16, 16], [0, 16]]}}), encoding="utf-8")
    manifest = tmp_path / "sample_manifest.json"
    manifest.write_text(json.dumps({"sample_id": "sample"}), encoding="utf-8")
    result = parse_output(image, arch, manifest, min_area=2)
    assert result["source"]["kind"] == "qwen_semantic_furniture_parse"
    assert result["source"]["qwen_generates_full_semantic"] is True
    assert len(result["objects"]) == 1
    assert result["objects"][0]["category"] == category
    assert result["objects"][0]["center_m"] is not None
