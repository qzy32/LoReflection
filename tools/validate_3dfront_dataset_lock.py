#!/usr/bin/env python3
"""Validate the frozen authoritative 3D-FRONT dataset lock."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from loreflection.config.paths import load_authoritative_3dfront_paths


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def count_model_info_entries(path: Path) -> int:
    data = load_json(path)
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        return len(data)
    raise ValueError(f"Unsupported model_info.json structure: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    lock = load_json(args.lock)
    paths = load_authoritative_3dfront_paths(args.env_file)
    failures: list[str] = []
    checks: dict[str, object] = {}

    expected = {
        "authoritative_root": paths.dataset_root.as_posix(),
        "scene_root": paths.scene_root.as_posix(),
        "future_model_root": paths.future_model_root.as_posix(),
        "future_model_info": paths.future_model_info.as_posix(),
        "texture_root": paths.texture_root.as_posix() if paths.texture_root else "",
    }
    for key, value in expected.items():
        checks[f"{key}_configured"] = value
        checks[f"{key}_locked"] = lock.get(key, "")
        if lock.get(key, "") != value:
            failures.append(f"{key} mismatch: configured={value} locked={lock.get(key, '')}")

    scene_jsons = sorted(paths.scene_root.glob("*.json"))
    checks["scene_json_count"] = len(scene_jsons)
    if len(scene_jsons) != lock.get("scene_json_count"):
        failures.append(f"scene_json_count mismatch: {len(scene_jsons)} != {lock.get('scene_json_count')}")

    model_info_count = count_model_info_entries(paths.future_model_info)
    checks["model_info_entry_count"] = model_info_count
    if model_info_count != lock.get("model_info_entry_count"):
        failures.append(f"model_info_entry_count mismatch: {model_info_count} != {lock.get('model_info_entry_count')}")

    manifest_path = args.lock.parent / "relative_file_manifest.txt"
    if not manifest_path.exists():
        failures.append(f"missing relative_file_manifest.txt next to lock: {manifest_path}")
    else:
        manifest_hash = sha256_file(manifest_path)
        checks["relative_manifest_sha256"] = manifest_hash
        if manifest_hash != lock.get("relative_manifest_sha256"):
            failures.append(
                f"relative manifest hash mismatch: {manifest_hash} != {lock.get('relative_manifest_sha256')}"
            )

    key_metadata_failures = []
    for rel_path, expected_hash in lock.get("key_metadata_sha256", {}).items():
        path = paths.dataset_root / rel_path
        if not path.exists():
            key_metadata_failures.append(f"missing key metadata: {rel_path}")
            continue
        actual = sha256_file(path)
        if actual != expected_hash:
            key_metadata_failures.append(f"hash mismatch for {rel_path}: {actual} != {expected_hash}")
    failures.extend(key_metadata_failures)
    checks["key_metadata_checked"] = len(lock.get("key_metadata_sha256", {}))

    sampled_scene_failures = []
    for rel_path, expected_hash in lock.get("sampled_scene_sha256", {}).items():
        path = paths.dataset_root / rel_path
        if not path.exists():
            sampled_scene_failures.append(f"missing sampled scene: {rel_path}")
            continue
        actual = sha256_file(path)
        if actual != expected_hash:
            sampled_scene_failures.append(f"sampled scene hash mismatch for {rel_path}: {actual} != {expected_hash}")
    failures.extend(sampled_scene_failures)
    checks["sampled_scene_checked"] = len(lock.get("sampled_scene_sha256", {}))

    report = {
        "lock": args.lock.as_posix(),
        "env_file": args.env_file.as_posix(),
        "dataset_lock_id": lock.get("dataset_lock_id"),
        "checks": checks,
        "failures": failures,
        "strict": bool(args.strict),
        "result": "pass" if not failures else "fail",
    }
    print(json.dumps(report, indent=2))
    if args.strict and failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
