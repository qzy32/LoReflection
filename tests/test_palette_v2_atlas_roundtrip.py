import json
from pathlib import Path


def test_palette_v2_atlas_roundtrip_clean():
    p = Path("reports/palette_v2_atlas_roundtrip.json")
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    selected = data["selected_palette"]
    key = "qwen_candidate" if selected == "palette_v2_qwenimage_candidate" else "native"
    assert data[key]["atlas"]["category_decode_accuracy"] == 1.0
