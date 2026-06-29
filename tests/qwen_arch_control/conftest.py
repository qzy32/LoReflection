import json
from pathlib import Path

import pytest


@pytest.fixture
def tiny_raw_3dfront_root(tmp_path: Path) -> Path:
    root = tmp_path / "3D-Front"
    scene_root = root / "3D-FRONT"
    future_root = root / "3D-FUTURE-model-part1"
    scene_root.mkdir(parents=True)
    future_root.mkdir(parents=True)
    model_info = [
        {"model_id": "jid_table", "category": "Coffee Table", "super-category": "Table"},
        {"model_id": "jid_chair", "category": "Dining Chair", "super-category": "Chair"},
    ]
    (future_root / "model_info.json").write_text(json.dumps(model_info), encoding="utf-8")
    scene = {
        "uid": "tiny_scene",
        "jobid": "tiny_house",
        "furniture": [
            {"uid": "table/model", "jid": "jid_table", "size": [1.2, 0.6, 0.8], "valid": True},
            {"uid": "chair/model", "jid": "jid_chair", "size": [0.6, 0.8, 0.6], "valid": True},
        ],
        "mesh": [
            {
                "uid": "floor/0",
                "type": "Floor",
                "xyz": [-2, 0, -2, 2, 0, -2, 2, 0, 2, -2, 0, 2],
            },
            {
                "uid": "window/0",
                "type": "Window",
                "xyz": [-1, 1, -2, 1, 1, -2, 1, 2, -2, -1, 2, -2],
            },
        ],
        "scene": {
            "room": [
                {
                    "instanceid": "DiningRoom-0",
                    "type": "DiningRoom",
                    "empty": False,
                    "children": [
                        {"ref": "table/model", "instanceid": "table_1", "pos": [0, 0, 0], "rot": [0, 0, 0, 1], "scale": [1, 1, 1]},
                        {"ref": "chair/model", "instanceid": "chair_1", "pos": [1, 0, 0], "rot": [0, 0, 0, 1], "scale": [1, 1, 1]},
                        {"ref": "floor/0", "instanceid": "floor_1", "pos": [0, 0, 0], "rot": [0, 0, 0, 1], "scale": [1, 1, 1]},
                        {"ref": "window/0", "instanceid": "window_1", "pos": [0, 0, 0], "rot": [0, 0, 0, 1], "scale": [1, 1, 1]},
                    ],
                }
            ]
        },
    }
    (scene_root / "tiny_scene.json").write_text(json.dumps(scene), encoding="utf-8")
    return root
