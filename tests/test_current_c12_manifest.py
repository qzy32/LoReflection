import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="legacy C12 semantic_repair4 manifest test retained for historical baseline only")


def test_c12_manifest_excludes_rotate_scale_from_semantic_metadata():
    manifest = json.loads(Path("reports/current_c12_input_manifest.json").read_text(encoding="utf-8"))
    assert manifest["semantic_repair4_actions"] == ["ADD", "REMOVE", "TRANSLATE", "REPLACE"]
    assert manifest["parametric_update_actions"] == ["ROTATE", "SCALE"]
    assert manifest["semantic_repair4_metadata_rows"] == 12
    assert {s["action"] for s in manifest["semantic_repair4_samples"]} == {"ADD", "REMOVE", "TRANSLATE", "REPLACE"}
    assert {s["action"] for s in manifest["excluded_from_diffsynth_metadata"]} == {"ROTATE", "SCALE"}


def test_c12_manifest_has_exact_sample_paths_and_metadata_rows():
    manifest = json.loads(Path("reports/current_c12_input_manifest.json").read_text(encoding="utf-8"))
    samples = manifest["semantic_repair4_samples"]
    assert len(samples) == 12
    required = {
        "sample_id",
        "action",
        "remote_sample_dir",
        "I_bad",
        "I_target",
        "control_mask",
        "mask_spec",
        "repairplan",
        "prompt",
        "metadata_row",
        "observer_status",
        "oracle_composite_status",
        "palette_validity",
        "same_class_merge",
    }
    for sample in samples:
        assert required <= sample.keys()
        base = sample["remote_sample_dir"]
        assert sample["I_bad"] == f"{base}/I_bad.png"
        assert sample["I_target"] == f"{base}/I_target.png"
        assert sample["control_mask"] == f"{base}/control_mask.png"
        assert sample["metadata_row"]["image"] == sample["I_target"]
        assert sample["metadata_row"]["blockwise_controlnet_image"] == sample["I_bad"]
        assert sample["metadata_row"]["blockwise_controlnet_inpaint_mask"] == sample["control_mask"]
        assert sample["metadata_row"]["prompt"]
        assert sample["observer_status"] in {"PASS", "FAIL", "UNKNOWN"}
        assert sample["oracle_composite_status"] in {"PASS", "FAIL", "UNKNOWN"}
        assert sample["palette_validity"] in {"PASS", "FAIL", "UNKNOWN"}
        assert isinstance(sample["same_class_merge"], bool)


def test_c12_manifest_rejects_semantic_metadata_rows_for_parametric_actions():
    manifest = json.loads(Path("reports/current_c12_input_manifest.json").read_text(encoding="utf-8"))
    parametric_actions = set(manifest["parametric_update_actions"])
    assert not any(sample["action"] in parametric_actions for sample in manifest["semantic_repair4_samples"])


def test_c12_manifest_parametric_action_negative_case():
    manifest = json.loads(Path("reports/current_c12_input_manifest.json").read_text(encoding="utf-8"))
    bad = json.loads(json.dumps(manifest))
    bad["semantic_repair4_samples"].append(
        {
            "sample_id": "bad_parametric_row",
            "action": "ROTATE",
            "remote_sample_dir": "/tmp/bad",
            "I_bad": "/tmp/bad/I_bad.png",
            "I_target": "/tmp/bad/I_target.png",
            "control_mask": "/tmp/bad/control_mask.png",
            "mask_spec": "/tmp/bad/mask_spec.json",
            "repairplan": "/tmp/bad/repairplan.json",
            "prompt": "/tmp/bad/prompt.txt",
            "metadata_row": {
                "image": "/tmp/bad/I_target.png",
                "blockwise_controlnet_image": "/tmp/bad/I_bad.png",
                "blockwise_controlnet_inpaint_mask": "/tmp/bad/control_mask.png",
                "prompt": "bad",
            },
            "observer_status": "UNKNOWN",
            "oracle_composite_status": "UNKNOWN",
            "palette_validity": "UNKNOWN",
            "same_class_merge": False,
        }
    )
    parametric_actions = set(bad["parametric_update_actions"])
    assert any(sample["action"] in parametric_actions for sample in bad["semantic_repair4_samples"])
