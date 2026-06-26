import numpy as np
from PIL import Image

from loreflection.qwen_arch_control.metric_transform import build_metric_transform
from loreflection.qwen_arch_control.render_architecture_condition_metric import render_architecture_condition_metric
from loreflection.semantic_registry import load_registry


def test_metric_architecture_condition_renderer_is_architecture_only(tmp_path):
    registry = load_registry()
    boundary = [[0, 0], [4, 0], [4, 3], [0, 3]]
    arch = {
        "architecture_id": "s1",
        "boundary": {"polygon_m": boundary, "source": "room_floor_mesh"},
        "metric_transform": build_metric_transform(boundary),
        "anchors": [{"anchor_type": "door", "bbox_m": [1.0, 0.0, 2.0, 0.2]}],
    }
    out = tmp_path / "condition.png"
    report = render_architecture_condition_metric(arch, out, 256, registry)
    assert report["renderer"] == "render_architecture_condition_metric_v2"
    assert report["architecture_only"] is True
    assert report["condition_contains_furniture"] is False
    arr = np.array(Image.open(out).convert("RGB"))
    object_colors = {registry.id_to_rgb[sid] for sid in registry.object_ids}
    assert not any(tuple(int(v) for v in pixel) in object_colors for pixel in arr.reshape(-1, 3))
