from pathlib import Path

from loreflection.qwen_arch_control.raw_3dfront_adapter import (
    adapt_scene_file,
    hard_footprint_collision_pairs,
)
from loreflection.qwen_arch_control.source_resolver import load_model_info_index, probe_data_root


def test_raw_adapter_builds_room_layout(tiny_raw_3dfront_root):
    probe = probe_data_root(tiny_raw_3dfront_root)
    model_index = load_model_info_index([Path(path) for path in probe["model_info_paths"]])
    scene_path = next((tiny_raw_3dfront_root / "3D-FRONT").glob("*.json"))
    records = adapt_scene_file(scene_path, model_index, image_size=128)
    assert len(records) == 1
    record = records[0]
    assert record["architecture"]["boundary"]["source"] == "room_floor_mesh"
    assert len(record["layout"]["objects"]) == 2
    assert {obj["category"] for obj in record["layout"]["objects"]} == {"coffee_table", "dining_chair"}


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
