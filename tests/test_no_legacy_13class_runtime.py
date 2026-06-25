from __future__ import annotations

from pathlib import Path


PRODUCTION_DIRS = [
    "configs",
    "data_pipeline",
    "diffusion",
    "eval",
    "experiments",
    "loreflection",
    "runtime",
    "schemas",
    "scripts",
    "tools",
    "vlm",
]

FORBIDDEN = [
    "semantic_registry_v1",
    "palette_v1_frozen",
    "semantic_layout_overfit32_v1",
    "num_categories=13",
    "num_categories = 13",
    "category_count=13",
    "category_count = 13",
]


def test_no_legacy_13class_runtime_references():
    hits = []
    root = Path(".")
    for dirname in PRODUCTION_DIRS:
        base = root / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN:
                if token in text:
                    hits.append(f"{path}:{token}")
    assert hits == []
