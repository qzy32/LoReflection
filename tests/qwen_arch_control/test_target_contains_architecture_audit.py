from pathlib import Path

from PIL import Image

from loreflection.semantic_registry import load_registry
from scripts.qwen_arch_control.audit_target_contains_architecture import audit_pair


def test_audit_distinguishes_void_background_from_structural_architecture(tmp_path: Path) -> None:
    registry = load_registry()
    palette = registry.name_to_rgb
    context = Image.new("RGB", (8, 8), palette["floor"])
    target = Image.new("RGB", (8, 8), palette["void"])
    for x in range(2, 4):
        for y in range(2, 4):
            target.putpixel((x, y), palette["desk"])
    context_path = tmp_path / "context.png"
    target_path = tmp_path / "target.png"
    context.save(context_path)
    target.save(target_path)

    report = audit_pair(context_path, target_path)

    assert report["context_contains_furniture"] is False
    assert report["target_contains_architecture"] is False
    assert report["target_contains_furniture"] is True
    assert report["target_interpretation"] == "full_semantic"
