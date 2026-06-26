"""Resolve raw 3D-FRONT sources without assuming one directory spelling."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Iterator


FRONT_DIR_NAMES = ("3D-FRONT", "3D-Front", "3D_FRONT")
FUTURE_DIR_HINTS = ("3d-future", "3d_future", "3d-future-model")


def _find_named_dir(root: Path, names: tuple[str, ...]) -> Path | None:
    lowered = {name.lower() for name in names}
    children = [path for path in root.iterdir() if path.is_dir()]
    child_match = next((path for path in children if path.name.lower() in lowered), None)
    if child_match is not None:
        return child_match
    if root.name.lower() in lowered and any(root.glob("*.json")):
        return root
    return None


def probe_data_root(data_root: Path) -> dict[str, Any]:
    data_root = data_root.resolve()
    scene_root = _find_named_dir(data_root, FRONT_DIR_NAMES)
    if scene_root is None:
        scene_candidates = [
            path.parent
            for path in data_root.rglob("*.json")
            if path.parent.name.lower() in {name.lower() for name in FRONT_DIR_NAMES}
        ]
        scene_root = scene_candidates[0] if scene_candidates else None
    scene_jsons = sorted(scene_root.glob("*.json")) if scene_root else []
    model_info_paths = sorted(
        path
        for path in data_root.rglob("model_info.json")
        if any(hint in path.parent.name.lower() for hint in FUTURE_DIR_HINTS)
        or "future" in path.as_posix().lower()
    )
    texture_dirs = sorted(
        path for path in data_root.iterdir() if path.is_dir() and "texture" in path.name.lower()
    )
    model_dirs = sorted(
        path for path in data_root.iterdir() if path.is_dir() and "future" in path.name.lower()
    )
    return {
        "data_root": str(data_root),
        "data_root_exists": data_root.exists(),
        "scene_root": str(scene_root) if scene_root else None,
        "scene_json_count": len(scene_jsons),
        "model_info_paths": [str(path) for path in model_info_paths],
        "texture_dirs": [str(path) for path in texture_dirs],
        "model_dirs": [str(path) for path in model_dirs],
        "recommended_source_mode": "raw_3dfront" if scene_jsons else "real_scene_package",
    }


def load_model_info_index(model_info_paths: list[Path]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in model_info_paths:
        payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        entries = list(payload.values()) if isinstance(payload, dict) else payload
        for item in entries if isinstance(entries, list) else []:
            if not isinstance(item, dict):
                continue
            model_id = item.get("model_id") or item.get("jid") or item.get("id") or item.get("uid")
            if model_id and str(model_id) not in index:
                index[str(model_id)] = item
    return index


def iter_raw_scene_records(data_root: Path, seed: int = 4411) -> Iterator[dict[str, Any]]:
    probe = probe_data_root(data_root)
    if not probe["scene_root"]:
        raise FileNotFoundError(f"No 3D-FRONT scene directory found under {data_root}")
    paths = sorted(Path(probe["scene_root"]).glob("*.json"))
    random.Random(seed).shuffle(paths)
    for path in paths:
        yield {
            "sample_id": path.stem,
            "scene_id": path.stem,
            "house_id": None,
            "floorplan_id": None,
            "room_type": None,
            "source_scene_json": str(path),
            "architecture_candidate": None,
            "furniture_objects_candidate": None,
            "warnings": [],
        }
