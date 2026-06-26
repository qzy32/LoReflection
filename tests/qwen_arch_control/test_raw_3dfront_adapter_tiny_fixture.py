from pathlib import Path

from loreflection.qwen_arch_control.raw_3dfront_adapter import adapt_scene_file
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
