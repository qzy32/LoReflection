import csv
import json
from pathlib import Path

from loreflection.qwen_arch_control.prompt_labels.build_prompt_label_dataset import build_prompt_label_dataset
from loreflection.qwen_arch_control.metric_transform import build_metric_transform
from loreflection.qwen_arch_control.render_architecture_condition_metric import render_architecture_condition_metric
from loreflection.qwen_arch_control.render_target_semantic_layout import render_target_semantic_layout
from loreflection.semantic_registry import load_registry


def test_prompt_label_metadata_contract(tmp_path: Path):
    source = tmp_path / "source"
    for d in ["cond", "target", "meta"]:
        (source / d).mkdir(parents=True)
    registry = load_registry()
    sid = "s1"
    boundary = [[0,0],[4,0],[4,3],[0,3]]
    transform = build_metric_transform(boundary)
    arch = {"architecture_id": sid, "room_type": "bedroom", "boundary": {"polygon_m": boundary}, "metric_transform": transform, "anchors": [], "source": {"kind": "raw_3dfront"}}
    cat = registry.id_to_name[sorted(registry.object_ids)[0]]
    layout = {"sample_id": sid, "room_type": "bedroom", "objects": [{"instance_id": "o1", "category": cat, "center_m": [2,1], "size_m": [1,1], "orientation_deg": 0}], "source": {"source_scene_json": "/x.json"}}
    render_architecture_condition_metric(arch, source / "cond/s1_arch_condition.png", 256, registry)
    render_target_semantic_layout(layout, source / "target/s1_target_semantic.png", 256, registry, arch)
    (source / "meta/s1_architecture.json").write_text(json.dumps(arch), encoding="utf-8")
    (source / "meta/s1_layout.json").write_text(json.dumps(layout), encoding="utf-8")
    (source / "meta/s1_verifier_refs.json").write_text("{}", encoding="utf-8")
    with (source / "metadata.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"])
        writer.writeheader(); writer.writerow({"image":"target/s1_target_semantic.png","prompt":"Context_Control.","context_image":"cond/s1_arch_condition.png","sample_id":sid,"goal_lostate":"meta/g.json","prompt_package":"meta/p.json","verifier_refs":"meta/s1_verifier_refs.json"})
    result = build_prompt_label_dataset(source, tmp_path / "labels", tmp_path / "requests.jsonl")
    assert result["audit"]["variant_count_per_sample"] == 3
    assert (tmp_path / "labels/metadata_template_functional.csv").exists()
    assert (tmp_path / "requests.jsonl").exists()
