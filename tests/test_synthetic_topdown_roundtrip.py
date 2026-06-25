import json
from pathlib import Path


def test_synthetic_all_categories_v2():
    p = Path("reports/taxonomy_v2_synthetic_topdown_roundtrip.json")
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["fixture_A_all_categories"]["parsed_instances"] == 34
