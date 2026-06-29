import json
from pathlib import Path

from loreflection.qwen_arch_control.raw_3dfront_adapter import (
    adapt_scene_file,
    hard_footprint_collision_pairs,
    severe_oob_footprint_objects,
)
from loreflection.qwen_arch_control.source_resolver import load_model_info_index, probe_data_root


def _load_model_index(root: Path):
    probe = probe_data_root(root)
    return load_model_info_index([Path(path) for path in probe["model_info_paths"]])


def _scene_path(root: Path) -> Path:
    return next((root / "3D-FRONT").glob("*.json"))


def _load_scene(root: Path) -> dict:
    return json.loads(_scene_path(root).read_text(encoding="utf-8"))


def _write_scene(root: Path, scene: dict) -> None:
    _scene_path(root).write_text(json.dumps(scene), encoding="utf-8")


def test_raw_adapter_builds_room_layout(tiny_raw_3dfront_root):
    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), image_size=128)
    assert len(records) == 1
    record = records[0]
    assert record["architecture"]["boundary"]["source"] == "room_floor_mesh"
    assert len(record["layout"]["objects"]) == 2
    assert {obj["category"] for obj in record["layout"]["objects"]} == {"coffee_table", "dining_chair"}


def test_furniture_valid_false_is_not_collected(tiny_raw_3dfront_root):
    scene = _load_scene(tiny_raw_3dfront_root)
    scene["furniture"][1]["valid"] = False
    _write_scene(tiny_raw_3dfront_root, scene)
    drop_reports = []

    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), drop_reports=drop_reports)

    assert records == []
    assert drop_reports[-1]["room_drop_reason"] == "insufficient_mapped_objects"
    assert drop_reports[-1]["mapped_object_count"] == 1


def test_unreferenced_furniture_is_not_collected(tiny_raw_3dfront_root):
    scene = _load_scene(tiny_raw_3dfront_root)
    scene["furniture"].append({"uid": "unused/model", "jid": "jid_chair", "size": [0.6, 0.8, 0.6], "valid": True})
    _write_scene(tiny_raw_3dfront_root, scene)

    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), image_size=128)

    assert len(records) == 1
    assert {obj["source_object_id"] for obj in records[0]["layout"]["objects"]} == {"table/model", "chair/model"}


def test_invalid_tiny_scale_drops_whole_room(tiny_raw_3dfront_root):
    scene = _load_scene(tiny_raw_3dfront_root)
    scene["scene"]["room"][0]["children"][1]["scale"] = [1e-6, 1, 1]
    _write_scene(tiny_raw_3dfront_root, scene)
    drop_reports = []

    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), drop_reports=drop_reports)

    assert records == []
    assert drop_reports[-1]["room_drop_reason"] == "semlayoutdiff_invalid_scale"


def test_invalid_large_scale_drops_whole_room(tiny_raw_3dfront_root):
    scene = _load_scene(tiny_raw_3dfront_root)
    scene["scene"]["room"][0]["children"][1]["scale"] = [6, 1, 1]
    _write_scene(tiny_raw_3dfront_root, scene)
    drop_reports = []

    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), drop_reports=drop_reports)

    assert records == []
    assert drop_reports[-1]["room_drop_reason"] == "semlayoutdiff_invalid_scale"


def test_mapped_objects_less_than_two_drops_room(tiny_raw_3dfront_root):
    scene = _load_scene(tiny_raw_3dfront_root)
    scene["scene"]["room"][0]["children"] = [
        child for child in scene["scene"]["room"][0]["children"] if child["ref"] != "chair/model"
    ]
    _write_scene(tiny_raw_3dfront_root, scene)
    drop_reports = []

    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), drop_reports=drop_reports)

    assert records == []
    assert drop_reports[-1]["room_drop_reason"] == "insufficient_mapped_objects"
    assert drop_reports[-1]["mapped_object_count"] == 1


def test_inter_object_collision_is_audit_only_not_room_drop(tiny_raw_3dfront_root):
    scene = _load_scene(tiny_raw_3dfront_root)
    scene["scene"]["room"][0]["children"][1]["pos"] = [0, 0, 0]
    _write_scene(tiny_raw_3dfront_root, scene)
    drop_reports = []

    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), drop_reports=drop_reports)

    assert len(records) == 1
    assert drop_reports == []
    collisions = records[0]["layout"]["inter_object_collision_pairs_for_audit"]
    assert collisions[0]["intersection_over_min_area"] > 0.5


def test_severe_oob_footprint_drops_whole_room(tiny_raw_3dfront_root):
    scene = _load_scene(tiny_raw_3dfront_root)
    scene["scene"]["room"][0]["children"][1]["pos"] = [10, 0, 10]
    _write_scene(tiny_raw_3dfront_root, scene)
    drop_reports = []

    records = adapt_scene_file(_scene_path(tiny_raw_3dfront_root), _load_model_index(tiny_raw_3dfront_root), drop_reports=drop_reports)

    assert records == []
    assert drop_reports[-1]["room_drop_reason"] == "severe_oob_footprint"
    assert drop_reports[-1]["severe_oob_objects"][0]["outside_area_ratio"] > 0.50


def test_severe_oob_ratio_at_or_below_threshold_does_not_drop():
    objects = [
        {
            "category": "wardrobe",
            "source_object_id": "wardrobe/model",
            "center_m": [0.5, 0.5],
            "footprint_m": [[-0.5, 0.0], [1.5, 0.0], [1.5, 1.0], [-0.5, 1.0]],
        }
    ]

    assert severe_oob_footprint_objects(objects, [[0, 0], [2, 0], [2, 2], [0, 2]]) == []


def test_severe_oob_ratio_above_threshold_drops():
    objects = [
        {
            "category": "wardrobe",
            "source_object_id": "wardrobe/model",
            "center_m": [-0.75, 0.5],
            "footprint_m": [[-2.0, 0.0], [0.5, 0.0], [0.5, 1.0], [-2.0, 1.0]],
        }
    ]

    oob = severe_oob_footprint_objects(objects, [[0, 0], [2, 0], [2, 2], [0, 2]])

    assert len(oob) == 1
    assert oob[0]["outside_area_ratio"] > 0.50


def test_center_outside_boundary_bbox_is_audit_only():
    objects = [
        {
            "category": "wardrobe",
            "source_object_id": "wardrobe/model",
            "center_m": [3.0, 3.0],
            "footprint_m": [[0.25, 0.25], [0.75, 0.25], [0.75, 0.75], [0.25, 0.75]],
        }
    ]

    assert severe_oob_footprint_objects(objects, [[0, 0], [2, 0], [2, 2], [0, 2]]) == []


def test_hard_footprint_collision_pairs_detects_bad_overlap():
    objects = [
        {
            "category": "dining_table",
            "source_object_id": "table/model",
            "footprint_m": [[0, 0], [2, 0], [2, 1], [0, 1]],
        },
        {
            "category": "dining_chair",
            "source_object_id": "chair/model",
            "footprint_m": [[0.2, 0.1], [1.8, 0.1], [1.8, 0.9], [0.2, 0.9]],
        },
    ]

    collisions = hard_footprint_collision_pairs(objects)

    assert len(collisions) == 1
    assert collisions[0]["intersection_over_min_area"] > 0.5


def test_lamps_do_not_participate_in_hard_footprint_collisions():
    objects = [
        {
            "category": "pendant_lamp",
            "source_object_id": "lamp/model",
            "footprint_m": [[0, 0], [2, 0], [2, 1], [0, 1]],
        },
        {
            "category": "double_bed",
            "source_object_id": "bed/model",
            "footprint_m": [[0.2, 0.1], [1.8, 0.1], [1.8, 0.9], [0.2, 0.9]],
        },
        {
            "category": "ceiling_lamp",
            "source_object_id": "ceiling/model",
            "footprint_m": [[0.2, 0.1], [1.8, 0.1], [1.8, 0.9], [0.2, 0.9]],
        },
    ]

    assert hard_footprint_collision_pairs(objects) == []


def test_hard_collision_gate_is_documented_as_loreflection_only():
    assert "LoReflection clean-data sanity gate" in (hard_footprint_collision_pairs.__doc__ or "")
    assert "not a SemLayoutDiff baseline rule" in (hard_footprint_collision_pairs.__doc__ or "")
