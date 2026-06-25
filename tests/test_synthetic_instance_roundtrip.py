from pathlib import Path
import json


def test_synthetic_isolated_instances_pass():
    report = Path("reports/synthetic_observer_roundtrip.json")
    if not report.exists():
        return
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["A_all_categories"]["category_accuracy"] == 1.0
    assert payload["B_repeated_separated"]["parsed_instances"] == 2
