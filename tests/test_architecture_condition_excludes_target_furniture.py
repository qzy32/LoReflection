from pathlib import Path

from PIL import Image

from tools.audit_architecture_condition_no_furniture import audit_image


def test_architecture_condition_allows_floor_color(tmp_path):
    image = tmp_path / "arch_condition.png"
    Image.new("RGB", (8, 8), (210, 210, 210)).save(image)
    report = audit_image(image, Path("artifacts/semantic_registry_v2"))
    assert report["status"] == "pass"


def test_architecture_condition_rejects_furniture_color(tmp_path):
    image = tmp_path / "arch_condition.png"
    Image.new("RGB", (8, 8), (72, 224, 199)).save(image)
    report = audit_image(image, Path("artifacts/semantic_registry_v2"))
    assert report["status"] == "fail"
    assert report["furniture_color_violations"]

