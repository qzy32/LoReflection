import numpy as np

from loreflection.qwen_arch_control.metric_transform import build_metric_transform, pixel_to_world, world_to_pixel


def test_metric_transform_roundtrip_p95_under_five_cm():
    room = [[-2.0, -1.5], [2.0, -1.5], [2.0, 1.5], [-2.0, 1.5]]
    transform = build_metric_transform(room, image_size_px=256, canvas_extent_m=8.0)
    errors = []
    for x in np.linspace(-1.8, 1.8, 9):
        for z in np.linspace(-1.3, 1.3, 9):
            px = world_to_pixel((float(x), float(z)), transform)
            wx, wz = pixel_to_world(px, transform)
            errors.append(((wx - x) ** 2 + (wz - z) ** 2) ** 0.5)
    assert np.percentile(errors, 95) <= 0.05
    assert transform["scale_policy"] == "fixed_metric_canvas"
