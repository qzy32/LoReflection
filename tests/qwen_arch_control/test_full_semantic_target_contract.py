from pathlib import Path

from PIL import Image

from loreflection.qwen_arch_control.render_full_semantic_target import compose_full_semantic_target
from loreflection.semantic_registry import load_registry
from scripts.qwen_arch_control.audit_full_semantic_target_contract import audit


def test_full_semantic_target_preserves_architecture_and_adds_furniture(tmp_path: Path) -> None:
    registry = load_registry()
    palette = registry.name_to_rgb
    context = Image.new("RGB", (8, 8), palette["floor"])
    for x in range(8):
        context.putpixel((x, 0), palette["door"])
    furniture = Image.new("RGB", (8, 8), palette["void"])
    for x in range(2, 5):
        for y in range(2, 5):
            furniture.putpixel((x, y), palette["desk"])
    context_path = tmp_path / "context.png"
    furniture_path = tmp_path / "furniture.png"
    full_path = tmp_path / "full.png"
    context.save(context_path)
    furniture.save(furniture_path)

    compose_report = compose_full_semantic_target(
        context_image_path=context_path,
        furniture_target_path=furniture_path,
        output_path=full_path,
        registry=registry,
    )
    audit_report = audit(context_path, furniture_path, full_path)

    assert compose_report["palette_exact"] is True
    assert compose_report["protected_architecture_overwrite_pixels"] == 0
    assert audit_report["status"] == "pass"
    assert audit_report["target_full_contains_architecture_categories"] is True
    assert audit_report["target_full_contains_furniture_categories"] is True
