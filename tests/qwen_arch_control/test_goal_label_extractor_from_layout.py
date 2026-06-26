import json

from loreflection.qwen_arch_control.goal_label_extractor_from_layout import extract_goal_lostate


def test_goal_extractor_drops_numeric_pose_and_provenance():
    layout = {
        "sample_id": "sample",
        "room_type": "diningroom",
        "objects": [
            {
                "category": "dining_table",
                "center_m": [0, 0],
                "size_m": [1, 1],
                "bbox_px": [1, 2, 3, 4],
                "source_json_path": "/private/source.json",
            }
        ],
        "source": {"kind": "raw_3dfront"},
    }
    architecture = {"architecture_id": "arch", "anchors": []}
    goal = extract_goal_lostate(layout, architecture)
    text = json.dumps(goal)
    for forbidden in ("center_m", "size_m", "bbox", "footprint", "source_json_path"):
        assert forbidden not in text
