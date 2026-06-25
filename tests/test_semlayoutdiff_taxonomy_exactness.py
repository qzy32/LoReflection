import json
from pathlib import Path


def test_semlayoutdiff_taxonomy_has_38_classes():
    p = Path("reports/semlayoutdiff_native_taxonomy_v2.json")
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    taxonomy = data["taxonomy"]
    assert len(taxonomy) == 38
    assert taxonomy[0]["category_name"] == "void"
    assert taxonomy[1]["category_name"] == "floor"
    assert taxonomy[36]["category_name"] == "door"
    assert taxonomy[37]["category_name"] == "window"
