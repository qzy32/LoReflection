"""Authoritative dataset path loading.

Runtime tools should resolve 3D-FRONT/3D-FUTURE paths through this module
instead of carrying server-specific defaults. Resolution order is:

1. explicit CLI overrides,
2. ``paths.local.env``,
3. process environment.

The legacy EditRoom path is intentionally not a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


class MissingAuthoritativeDatasetConfig(RuntimeError):
    """Raised when required authoritative dataset paths are not configured."""


def read_env_file(path: Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path:
        return values
    if not path.exists():
        raise FileNotFoundError(f"Missing env file: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class Authoritative3DFrontPaths:
    dataset_root: Path
    scene_root: Path
    future_model_root: Path
    future_model_info: Path
    texture_root: Path | None = None


def _pick(name: str, env_file_values: dict[str, str], explicit: dict[str, str | Path | None]) -> str:
    value = explicit.get(name)
    if value:
        return str(value)
    if env_file_values.get(name):
        return env_file_values[name]
    if os.environ.get(name):
        return os.environ[name]
    return ""


def load_authoritative_3dfront_paths(
    env_file: Path | None,
    *,
    scene_root: str | Path | None = None,
    future_model_root: str | Path | None = None,
    future_model_info: str | Path | None = None,
    texture_root: str | Path | None = None,
    dataset_root: str | Path | None = None,
) -> Authoritative3DFrontPaths:
    env_values = read_env_file(env_file)
    explicit = {
        "THREED_FRONT_DATASET_ROOT": dataset_root,
        "THREED_FRONT_SCENE_ROOT": scene_root,
        "THREED_FUTURE_MODEL_ROOT": future_model_root,
        "THREED_FUTURE_MODEL_INFO": future_model_info,
        "THREED_FRONT_TEXTURE_ROOT": texture_root,
    }

    root_text = _pick("THREED_FRONT_DATASET_ROOT", env_values, explicit)
    scene_text = _pick("THREED_FRONT_SCENE_ROOT", env_values, explicit)
    future_root_text = _pick("THREED_FUTURE_MODEL_ROOT", env_values, explicit)
    model_info_text = _pick("THREED_FUTURE_MODEL_INFO", env_values, explicit)
    texture_text = _pick("THREED_FRONT_TEXTURE_ROOT", env_values, explicit)

    # Backward-compatible explicit variable support for old env files. This is
    # not a hardcoded path fallback and still requires user/server config.
    if not scene_text:
        scene_text = env_values.get("THREED_FRONT_ROOT", "") or os.environ.get("THREED_FRONT_ROOT", "")
    if not future_root_text:
        future_root_text = env_values.get("THREED_FUTURE_ROOT", "") or os.environ.get("THREED_FUTURE_ROOT", "")
    if not root_text and scene_text:
        candidate = Path(scene_text)
        root_text = str(candidate.parent if candidate.name == "3D-FRONT" else candidate)
    if not model_info_text and future_root_text:
        candidate = Path(future_root_text) / "model_info.json"
        if candidate.exists():
            model_info_text = str(candidate)

    missing = [
        name
        for name, value in [
            ("THREED_FRONT_DATASET_ROOT", root_text),
            ("THREED_FRONT_SCENE_ROOT", scene_text),
            ("THREED_FUTURE_MODEL_ROOT", future_root_text),
            ("THREED_FUTURE_MODEL_INFO", model_info_text),
        ]
        if not value
    ]
    if missing:
        raise MissingAuthoritativeDatasetConfig(
            "Missing authoritative 3D-FRONT dataset configuration. "
            f"Missing: {', '.join(missing)}"
        )

    paths = Authoritative3DFrontPaths(
        dataset_root=Path(root_text),
        scene_root=Path(scene_text),
        future_model_root=Path(future_root_text),
        future_model_info=Path(model_info_text),
        texture_root=Path(texture_text) if texture_text else None,
    )
    for label, path in [
        ("THREED_FRONT_DATASET_ROOT", paths.dataset_root),
        ("THREED_FRONT_SCENE_ROOT", paths.scene_root),
        ("THREED_FUTURE_MODEL_ROOT", paths.future_model_root),
        ("THREED_FUTURE_MODEL_INFO", paths.future_model_info),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} does not exist: {path}")
    if paths.texture_root is not None and not paths.texture_root.exists():
        raise FileNotFoundError(f"THREED_FRONT_TEXTURE_ROOT does not exist: {paths.texture_root}")
    return paths
