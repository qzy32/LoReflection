import csv
import json
from pathlib import Path

from loreflection.qwen_arch_control.audit_architecture_condition_scale import audit_dataset


def test_scale_audit_records_missing_explicit_metric_transform(tmp_path: Path):
    root = tmp_path / "dataset"
    (root / "meta").mkdir(parents=True)
    with (root / "metadata.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id"])
        writer.writeheader()
        writer.writerow({"image": "target/s1.png", "prompt": "Context_Control. bedroom", "context_image": "cond/s1.png", "sample_id": "s1"})
    (root / "meta" / "s1_architecture.json").write_text(json.dumps({"boundary": {"polygon_m": [[0, 0], [4, 0], [4, 3], [0, 3]], "polygon_px": [[10, 10], [246, 10], [246, 246], [10, 246]], "boundary_source": "room_bbox"}}), encoding="utf-8")
    (root / "meta" / "s1_layout.json").write_text(json.dumps({"room_type": "bedroom", "source": {"source_scene_json": "/data/scene.json"}, "objects": [{"center_m": [1, 1], "size_m": [1, 1], "orientation_deg": 0}]}), encoding="utf-8")
    (root / "meta" / "s1_sample_manifest.json").write_text(json.dumps({"sample_id": "s1", "room_type": "bedroom"}), encoding="utf-8")
    report = audit_dataset(root)
    assert report["qwen_generates_architecture"] is False
    assert report["qwen_generates_furniture_only"] is True
    assert report["metric_transform_exists_rate"] == 0.0
    assert report["implicit_transform_recoverable"] is True
    assert report["metric_v2_recommended"] is True
