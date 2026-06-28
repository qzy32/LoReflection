import random
from io import BytesIO

import numpy as np

from loreflection.qwen_arch_control.semantic_topdown_renderer import (
    render_full_semantic_target_image,
    semantic_render_priority,
)
from loreflection.semantic_registry import load_registry


def _png_bytes(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _architecture(with_door=False):
    anchors = []
    if with_door:
        anchors.append({"anchor_id": "door_0", "anchor_type": "door", "bbox_px": [14, 0, 18, 4]})
    return {
        "image_size_px": [32, 32],
        "boundary": {"polygon_px": [[2, 2], [29, 2], [29, 29], [2, 29]], "boundary_source": "test"},
        "anchors": anchors,
    }


def _obj(instance_id, category, bbox):
    x0, y0, x1, y1 = bbox
    return {
        "instance_id": instance_id,
        "category": category,
        "footprint_px": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
    }


def _render(objects, with_door=False):
    img, report = render_full_semantic_target_image(_architecture(with_door=with_door), {"objects": objects})
    return img, report


def test_render_order_is_permutation_stable():
    objects = [
        _obj("table", "coffee_table", [6, 6, 24, 24]),
        _obj("chair", "chair", [9, 9, 18, 18]),
        _obj("lamp", "pendant_lamp", [12, 12, 16, 16]),
    ]
    baseline, _ = _render(objects)
    baseline_bytes = _png_bytes(baseline)
    rng = random.Random(4411)
    for _ in range(5):
        shuffled = list(objects)
        rng.shuffle(shuffled)
        img, _ = _render(shuffled)
        assert _png_bytes(img) == baseline_bytes


def test_high_priority_lamp_renders_last_over_normal_furniture():
    registry = load_registry()
    img, report = _render([
        _obj("table", "coffee_table", [6, 6, 24, 24]),
        _obj("lamp", "pendant_lamp", [12, 12, 16, 16]),
    ])
    arr = np.asarray(img)
    assert tuple(arr[14, 14]) == registry.name_to_rgb["pendant_lamp"]
    orders = {r["category"]: r["render_order_index"] for r in report["object_reports"]}
    assert orders["pendant_lamp"] > orders["coffee_table"]
    assert any(r["overwritten_previous_furniture_px"] > 0 for r in report["object_reports"] if r["category"] == "pendant_lamp")


def test_low_priority_air_conditioner_policy_sorts_before_normal():
    assert semantic_render_priority("air_conditioner") < semantic_render_priority("coffee_table")
    assert semantic_render_priority("ceiling_air_conditioner") < semantic_render_priority("sofa")


def test_protected_pixels_unchanged_independent_of_priority():
    registry = load_registry()
    objects = [
        _obj("table", "coffee_table", [10, 0, 22, 10]),
        _obj("lamp", "ceiling_lamp", [12, 0, 20, 8]),
    ]
    img, report = _render(objects, with_door=True)
    arr = np.asarray(img)
    door_rgb = registry.name_to_rgb["door"]
    assert tuple(arr[2, 16]) == door_rgb
    assert report["protected_pixels_unchanged"] is True
    assert report["door_window_overwritten_pixels_after_write"] == 0


def test_render_output_palette_exact():
    registry = load_registry()
    img, _ = _render([
        _obj("table", "coffee_table", [6, 6, 24, 24]),
        _obj("lamp", "ceiling_lamp", [12, 12, 16, 16]),
    ])
    allowed = {tuple(v) for v in registry.name_to_rgb.values()}
    colors = {tuple(int(x) for x in rgb) for rgb in np.asarray(img).reshape(-1, 3)}
    assert colors <= allowed
