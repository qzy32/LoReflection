import csv
import json
from pathlib import Path

from PIL import Image

from loreflection.qwen_arch_control.audit_architecture_condition_scale import audit_dataset
from loreflection.qwen_arch_control.metric_transform import build_metric_transform, world_to_pixel
from loreflection.qwen_arch_control.render_architecture_condition_metric import render_architecture_condition_metric
from loreflection.qwen_arch_control.render_target_semantic_layout import render_target_semantic_layout
from loreflection.semantic_registry import load_registry


def test_metric_v2_dataset_contract_on_tiny_package(tmp_path: Path):
    registry = load_registry()
    root = tmp_path / "dataset"
    for name in ["cond", "target", "meta", "audits"]:
        (root / name).mkdir(parents=True)
    sid = "s1"
    boundary = [[0, 0], [4, 0], [4, 3], [0, 3]]
    transform = build_metric_transform(boundary, image_size_px=256, canvas_extent_m=8.0)
    polygon_px = [list(world_to_pixel((p[0], p[1]), transform)) for p in boundary]
    arch = {
        "architecture_id": sid,
        "boundary": {"polygon_m": boundary, "polygon_px": polygon_px, "source": "room_floor_mesh", "boundary_source": "room_floor_mesh"},
        "metric_transform": transform,
        "source": {"kind": "raw_3dfront"},
    }
    category = registry.id_to_name[sorted(registry.object_ids)[0]]
    layout = {
        "room_type": "bedroom",
        "source": {"source_scene_json": "/data/scene.json"},
        "metric_transform": transform,
        "objects": [{"instance_id": "obj1", "category": category, "center_m": [2, 1.5], "size_m": [1, 0.8], "orientation_deg": 0}],
    }
    cond_report = render_architecture_condition_metric(arch, root / "cond" / f"{sid}_arch_condition.png", 256, registry)
    target_report = render_target_semantic_layout(layout, root / "target" / f"{sid}_target_semantic.png", 256, registry, arch)
    (root / "meta" / "p0_dataset_manifest.json").write_text(json.dumps({"renderer_version": "metric_v2"}), encoding="utf-8")
    (root / "meta" / f"{sid}_architecture.json").write_text(json.dumps(arch), encoding="utf-8")
    (root / "meta" / f"{sid}_layout.json").write_text(json.dumps(layout), encoding="utf-8")
    (root / "meta" / f"{sid}_sample_manifest.json").write_text(json.dumps({"sample_id": sid, "room_type": "bedroom", "renderer_version": "metric_v2", "metric_transform": transform, "condition_contract": cond_report, "target_contract": target_report}), encoding="utf-8")
    with (root / "metadata.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id"])
        writer.writeheader()
        writer.writerow({"image": f"target/{sid}_target_semantic.png", "prompt": "Context_Control. bedroom", "context_image": f"cond/{sid}_arch_condition.png", "sample_id": sid})
    report = audit_dataset(root)
    assert report["metric_transform_exists_rate"] == 1.0
    assert report["roundtrip_error_p95_m"] <= 0.05
    assert report["target_bbox_fallback_rate"] == 0.0
    assert report["status"] == "pass"
