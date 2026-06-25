import json
from pathlib import Path


def test_condition_to_target_remap():
    p = Path("configs/semantic_target_registry_v2_candidate.yaml")
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["architecture_condition_to_target_remap"]["2"] == 36
    assert data["architecture_condition_to_target_remap"]["3"] == 37
