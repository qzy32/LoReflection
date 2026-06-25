from __future__ import annotations

import pytest

from loreflection.semantic_registry import LegacySemanticRegistryError, load_registry


def test_single_semantic_registry_source_is_v2():
    registry = load_registry()
    assert len(registry.categories) == 38
    assert registry.id_to_name[0] == "void"
    assert registry.id_to_name[1] == "floor"
    assert registry.id_to_name[36] == "door"
    assert registry.id_to_name[37] == "window"
    assert len(registry.object_ids) == 34
    assert registry.registry_hash


def test_legacy_registry_hard_fails():
    with pytest.raises(LegacySemanticRegistryError):
        load_registry("artifacts/semantic_registry_v1")
