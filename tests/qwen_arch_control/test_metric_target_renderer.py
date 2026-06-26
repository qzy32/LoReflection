from PIL import Image

from loreflection.qwen_arch_control.metric_transform import build_metric_transform
from loreflection.qwen_arch_control.render_target_semantic_layout import render_target_semantic_layout
from loreflection.semantic_registry import load_registry


def test_metric_target_renderer_uses_metric_transform_and_no_bbox_fallback(tmp_path):
    registry = load_registry()
    category = registry.id_to_name[sorted(registry.object_ids)[0]]
    boundary = [[0, 0], [4, 0], [4, 3], [0, 3]]
    arch = {"metric_transform": build_metric_transform(boundary), "boundary": {"polygon_m": boundary}}
    layout = {
        "objects": [{
            "instance_id": "obj1",
            "category": category,
            "center_m": [2.0, 1.5],
            "size_m": [1.0, 0.6],
            "orientation_deg": 15,
        }]
    }
    report = render_target_semantic_layout(layout, tmp_path / "target.png", 256, registry, arch)
    assert report["uses_metric_transform"] is True
    assert report["target_bbox_fallback_rate"] == 0.0
    assert report["rendered_objects"][0]["render_source"] == "center_size_orientation"
    assert Image.open(tmp_path / "target.png").size == (256, 256)
