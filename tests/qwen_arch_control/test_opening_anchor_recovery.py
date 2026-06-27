from __future__ import annotations

from loreflection.qwen_arch_control.opening_anchor_recovery import (
    collect_scene_opening_candidates,
    recover_opening_anchors_for_room,
)
from loreflection.qwen_arch_control.metric_transform import build_metric_transform
from loreflection.qwen_arch_control.semantic_topdown_renderer import render_architecture_condition_image


def _door_mesh(uid: str = "door_mesh", x: float = 1.0, z0: float = -0.05, z1: float = 0.05):
    return {"uid": uid, "type": "Door", "xyz": [x, 0, z0, x, 0, z1, x + 0.2, 0, z1, x + 0.2, 0, z0]}


def test_scene_level_door_candidate_assigned_to_boundary_room():
    scene = {"mesh": [_door_mesh()], "scene": {"room": []}, "furniture": []}
    candidates = collect_scene_opening_candidates(scene, {})
    anchors = recover_opening_anchors_for_room(candidates, [[0, 0], [2, 0], [2, 2], [0, 2]], assigned_room_id="room")
    assert len(anchors) == 1
    assert anchors[0]["anchor_type"] == "door"
    assert anchors[0]["confidence"] >= 0.75


def test_scene_level_door_can_belong_to_two_adjacent_rooms():
    scene = {"mesh": [_door_mesh(x=2.0, z0=0.8, z1=1.2)], "scene": {"room": []}, "furniture": []}
    candidates = collect_scene_opening_candidates(scene, {})
    left = recover_opening_anchors_for_room(candidates, [[0, 0], [2, 0], [2, 2], [0, 2]], assigned_room_id="left")
    right = recover_opening_anchors_for_room(candidates, [[2, 0], [4, 0], [4, 2], [2, 2]], assigned_room_id="right")
    assert len(left) == 1
    assert len(right) == 1


def test_far_door_is_not_forced_into_room():
    scene = {"mesh": [_door_mesh(x=10.0)], "scene": {"room": []}, "furniture": []}
    candidates = collect_scene_opening_candidates(scene, {})
    anchors = recover_opening_anchors_for_room(candidates, [[0, 0], [2, 0], [2, 2], [0, 2]], assigned_room_id="room")
    assert anchors == []


def test_wardrobe_and_cabinet_doors_are_not_structural_candidates():
    scene = {
        "mesh": [],
        "furniture": [
            {"uid": "wardrobe/model", "jid": "w", "title": "wardrobe door", "type": "standard"},
            {"uid": "cabinet/model", "jid": "c", "title": "cabinet door", "type": "standard"},
        ],
        "scene": {"room": [{"children": [{"ref": "wardrobe/model", "pos": [1, 0, 0]}, {"ref": "cabinet/model", "pos": [1, 0, 0]}]}]},
    }
    assert collect_scene_opening_candidates(scene, {}) == []


def test_recovered_door_anchor_renders_door_pixels():
    scene = {"mesh": [_door_mesh(x=1.0, z0=-0.05, z1=0.05)], "scene": {"room": []}, "furniture": []}
    candidates = collect_scene_opening_candidates(scene, {})
    boundary = [[0, 0], [2, 0], [2, 2], [0, 2]]
    transform = build_metric_transform(boundary, 256, canvas_extent_m=8.0)
    anchors = recover_opening_anchors_for_room(candidates, boundary, assigned_room_id="room", metric_transform=transform)
    arch = {
        "image_size_px": [256, 256],
        "boundary": {"polygon_m": boundary, "boundary_source": "unit_test"},
        "metric_transform": transform,
        "anchors": anchors,
    }
    _, report = render_architecture_condition_image(arch)
    assert report["anchor_pixel_counts"]["door"] > 0


def test_major_room_without_recoverable_door_should_be_dropped_by_gate_logic():
    scene = {"mesh": [], "scene": {"room": []}, "furniture": []}
    candidates = collect_scene_opening_candidates(scene, {})
    anchors = recover_opening_anchors_for_room(candidates, [[0, 0], [2, 0], [2, 2], [0, 2]], assigned_room_id="bedroom")
    assert anchors == []
