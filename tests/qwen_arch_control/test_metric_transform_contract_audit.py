import csv
import json

from PIL import Image

from loreflection.qwen_arch_control.prompt_labels.audit_metric_transform_contract import audit_metric_transform_contract


def test_metric_transform_contract_audit_reads_explicit_transform(tmp_path):
    base = tmp_path
    (base / "meta").mkdir()
    Image.new("RGB", (256, 256), (0, 0, 0)).save(base / "target.png")
    Image.new("RGB", (256, 256), (0, 0, 0)).save(base / "cond.png")
    (base / "meta/sample_architecture.json").write_text(
        json.dumps({
            "metric_transform": {
                "pixels_per_meter": 32.0,
                "origin_world_m": [0.0, 0.0],
                "image_size_px": [256, 256],
                "room_bbox_m": [0.0, 0.0, 2.0, 2.0],
            }
        }),
        encoding="utf-8",
    )
    metadata = base / "metadata.csv"
    with metadata.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id"])
        writer.writeheader()
        writer.writerow({"image": "target.png", "prompt": "Context_Control.", "context_image": "cond.png", "sample_id": "sample"})
    report = audit_metric_transform_contract(metadata, base)
    assert report["same_resolution_rate"] == 1.0
    assert report["all_images_256x256_rate"] == 1.0
    assert report["metric_transform_exists_rate"] == 1.0
    assert report["pixels_per_meter_values"] == [32.0]
