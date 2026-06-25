"""Single runtime entry point for SemLayoutDiff-aligned semantic categories.

The production LoReflection semantic target registry is the 38-class
SemLayoutDiff-aligned registry under ``artifacts/semantic_registry_v2``.
Legacy 13-class artifacts are intentionally unsupported.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_ROOT = REPO_ROOT / "artifacts" / "semantic_registry_v2"


class LegacySemanticRegistryError(RuntimeError):
    """Raised when a deprecated 13-class artifact is passed to runtime code."""


@dataclass(frozen=True)
class SemanticCategory:
    semantic_id: int
    name: str
    role: str
    rgb: tuple[int, int, int]
    coarse_group: str


class SemanticRegistry:
    def __init__(self, root: Path | str = DEFAULT_REGISTRY_ROOT):
        self.root = Path(root)
        legacy_name = "semantic_registry_" + "v1"
        if self.root.name == legacy_name:
            raise LegacySemanticRegistryError(
                "Legacy 13-class artifact is unsupported. "
                "Rebuild the dataset with semantic_registry_v2."
            )
        self.target_path = self.root / "semantic_target_registry.json"
        self.palette_path = self.root / "palette_frozen.json"
        if not self.target_path.exists() or not self.palette_path.exists():
            raise FileNotFoundError(f"Missing semantic_registry_v2 files under {self.root}")
        self._target = _read_json(self.target_path)
        self._palette = _read_json(self.palette_path)
        self.registry_hash = _hash_files([self.target_path, self.palette_path])
        self.categories = self._load_categories()

    def _load_categories(self) -> list[SemanticCategory]:
        entries = self._target.get("categories", self._target)
        if isinstance(entries, dict):
            entries = list(entries.values())
        palette = self._palette.get("colors", self._palette)
        categories: list[SemanticCategory] = []
        seen_ids: set[int] = set()
        seen_rgb: set[tuple[int, int, int]] = set()
        for entry in entries:
            sid = int(entry["semantic_id"])
            name = str(entry.get("category_name") or entry.get("name"))
            color = palette.get(name) or entry.get("RGB")
            if isinstance(color, str):
                rgb = _hex_to_rgb(color)
            else:
                rgb = tuple(int(v) for v in color)
            if sid in seen_ids:
                raise ValueError(f"Duplicate semantic_id in registry: {sid}")
            if rgb in seen_rgb:
                raise ValueError(f"Duplicate RGB in production registry: {rgb}")
            seen_ids.add(sid)
            seen_rgb.add(rgb)
            categories.append(
                SemanticCategory(
                    semantic_id=sid,
                    name=name,
                    role=str(entry.get("role") or entry.get("category_role") or "object"),
                    rgb=rgb,
                    coarse_group=str(entry.get("coarse_group") or "ungrouped"),
                )
            )
        categories.sort(key=lambda c: c.semantic_id)
        if len(categories) != 38:
            raise ValueError(f"Expected 38 semantic categories, got {len(categories)}")
        return categories

    @property
    def id_to_name(self) -> dict[int, str]:
        return {c.semantic_id: c.name for c in self.categories}

    @property
    def name_to_id(self) -> dict[str, int]:
        return {c.name: c.semantic_id for c in self.categories}

    @property
    def name_to_rgb(self) -> dict[str, tuple[int, int, int]]:
        return {c.name: c.rgb for c in self.categories}

    @property
    def id_to_rgb(self) -> dict[int, tuple[int, int, int]]:
        return {c.semantic_id: c.rgb for c in self.categories}

    @property
    def object_ids(self) -> set[int]:
        return {c.semantic_id for c in self.categories if c.role == "object"}

    def colorize_label(self, semantic_id: int) -> tuple[int, int, int]:
        return self.id_to_rgb[int(semantic_id)]


def load_registry(root: Path | str = DEFAULT_REGISTRY_ROOT) -> SemanticRegistry:
    return SemanticRegistry(root)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def _hash_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        h.update(path.as_posix().encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
