import json
from pathlib import Path


def test_pipeline_modes_recorded():
    p = Path("reports/semlayoutdiff_compatible_pipeline_v2.json")
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "semlayoutdiff_bbox" in data["bbox_compatibility_mode"]
    assert "footprint" in data["footprint_loreflection_mode"]
