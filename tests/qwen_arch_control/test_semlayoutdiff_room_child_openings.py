
from __future__ import annotations

from loreflection.qwen_arch_control.raw_3dfront_adapter import collect_room_child_openings_sem_layoutdiff_style
from loreflection.qwen_arch_control.semantic_topdown_renderer import render_architecture_condition_image
from loreflection.qwen_arch_control.metric_transform import build_metric_transform


def _mesh(uid: str, typ: str):
    return {"uid": uid, "type": typ, "xyz": [0, 0, 0, 1, 0, 0, 1, 0, 0.1, 0, 0, 0.1]}


def test_scene_global_door_without_room_child_ref_is_not_counted():
    scene = {"mesh": [_mesh("door_a", "Door")], "scene": {"room": [{"children": []}]}}
    anchors = collect_room_child_openings_sem_layoutdiff_style(scene, scene["scene"]["room"][0], assigned_room_id="room")
    assert anchors == []


def test_room_child_door_mesh_ref_is_counted():
    scene = {"mesh": [_mesh("door_a", "Door")], "scene": {"room": [{"children": [{"ref": "door_a"}]}]}}
    anchors = collect_room_child_openings_sem_layoutdiff_style(scene, scene["scene"]["room"][0], assigned_room_id="room")
    assert len(anchors) == 1
    assert anchors[0]["anchor_type"] == "door"
    assert anchors[0]["source_policy"] == "semlayoutdiff_room_children_only"


def test_scene_global_window_without_room_child_ref_is_not_counted():
    scene = {"mesh": [_mesh("window_a", "Window")], "scene": {"room": [{"children": []}]}}
    anchors = collect_room_child_openings_sem_layoutdiff_style(scene, scene["scene"]["room"][0], assigned_room_id="room")
    assert anchors == []


def test_room_child_window_mesh_ref_is_counted():
    scene = {"mesh": [_mesh("window_a", "Window")], "scene": {"room": [{"children": [{"ref": "window_a"}]}]}}
    anchors = collect_room_child_openings_sem_layoutdiff_style(scene, scene["scene"]["room"][0], assigned_room_id="room")
    assert len(anchors) == 1
    assert anchors[0]["anchor_type"] == "window"


def test_renderer_does_not_fabricate_door_when_no_anchor():
    boundary = [[0, 0], [2, 0], [2, 2], [0, 2]]
    arch = {"image_size_px": [256, 256], "boundary": {"polygon_m": boundary}, "metric_transform": build_metric_transform(boundary), "anchors": []}
    _, report = render_architecture_condition_image(arch)
    assert report["anchor_counts"]["door"] == 0
    assert report["anchor_pixel_counts"]["door"] == 0


def test_door_anchor_renders_door_pixels():
    scene = {"mesh": [_mesh("door_a", "Door")], "scene": {"room": [{"children": [{"ref": "door_a"}]}]}}
    anchors = collect_room_child_openings_sem_layoutdiff_style(scene, scene["scene"]["room"][0], assigned_room_id="room")
    boundary = [[0, 0], [2, 0], [2, 2], [0, 2]]
    arch = {"image_size_px": [256, 256], "boundary": {"polygon_m": boundary}, "metric_transform": build_metric_transform(boundary), "anchors": anchors}
    _, report = render_architecture_condition_image(arch)
    assert report["anchor_counts"]["door"] == 1
    assert report["anchor_pixel_counts"]["door"] > 0


def test_require_room_child_door_gate_drop_reason():
    scene = {"mesh": [_mesh("door_a", "Door")], "scene": {"room": [{"children": []}]}}
    anchors = collect_room_child_openings_sem_layoutdiff_style(scene, scene["scene"]["room"][0], assigned_room_id="room")
    drop_reason = "" if any(a["anchor_type"] == "door" for a in anchors) else "drop_no_room_child_door_anchor"
    assert drop_reason == "drop_no_room_child_door_anchor"
