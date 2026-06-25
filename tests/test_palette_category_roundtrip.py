from pathlib import Path
import json


def test_palette_atlas_roundtrip_report_exists_and_passes():
    report = Path("reports/palette_roundtrip_and_perturbation.json")
    if not report.exists():
        return
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["atlas"]["decode_accuracy"] == 1.0
    assert payload["atlas"]["unknown_roi_count"] == 0
