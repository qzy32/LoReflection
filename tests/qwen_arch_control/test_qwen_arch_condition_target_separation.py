import csv
from pathlib import Path

from PIL import Image

from loreflection.qwen_arch_control.build_qwen_arch_control_dataset import build_dataset
from loreflection.semantic_registry import load_registry


def _colors(path: Path):
    image = Image.open(path).convert("RGB")
    return {rgb for _, rgb in image.getcolors(maxcolors=image.width * image.height) or []}


def test_condition_excludes_furniture_and_target_contains_it(tmp_path: Path):
    root = tmp_path / "p0"
    build_dataset(root, num_samples=3, image_size=96, seed=17)
    registry = load_registry()
    furniture = {category.rgb for category in registry.categories if category.semantic_id in registry.object_ids}
    with (root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            assert not (_colors(root / row["context_image"]) & furniture)
            assert _colors(root / row["image"]) & furniture
