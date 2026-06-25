import json
from pathlib import Path


def test_no_aabb_target_gate():
    p = Path("reports/taxonomy_v2_gate_status.json")
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["LoReflection_mode_contains_no_bbox_conversion"] is True
