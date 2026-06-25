#!/usr/bin/env python
"""Inspect selected 3D-FRONT scene JSON structure.

This helper is read-only. It summarizes furniture metadata, scene room child
transform links, and mesh keys for a bounded set of selected scene JSON files.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def room_children(scene: dict[str, Any]) -> list[dict[str, Any]]:
    scene_obj = scene.get("scene", {})
    rooms = scene_obj.get("room") or scene_obj.get("rooms") if isinstance(scene_obj, dict) else []
    out: list[dict[str, Any]] = []
    if not isinstance(rooms, list):
        return out
    for room_index, room in enumerate(rooms):
        if not isinstance(room, dict):
            continue
        for child_index, child in enumerate(room.get("children", []) if isinstance(room.get("children"), list) else []):
            if isinstance(child, dict):
                item = dict(child)
                item["_path"] = f"scene.room[{room_index}].children[{child_index}]"
                out.append(item)
    return out


def inspect_scene(path: Path) -> dict[str, Any]:
    scene = load_json(path)
    furniture = [x for x in scene.get("furniture", []) if isinstance(x, dict)] if isinstance(scene, dict) else []
    uid_set = {str(x.get("uid")) for x in furniture if x.get("uid") is not None}
    jid_set = {str(x.get("jid")) for x in furniture if x.get("jid") is not None}
    link_counts = Counter()
    child_examples = []
    for child in room_children(scene):
        for child_key, target_name, target_set in [
            ("ref", "furniture.uid", uid_set),
            ("uid", "furniture.uid", uid_set),
            ("instanceid", "furniture.uid", uid_set),
            ("jid", "furniture.jid", jid_set),
            ("ref", "furniture.jid", jid_set),
        ]:
            value = child.get(child_key)
            if value is not None and str(value) in target_set:
                link_counts[f"child.{child_key} -> {target_name}"] += 1
        if len(child_examples) < 12:
            child_examples.append(
                {
                    "path": child.get("_path"),
                    "ref": child.get("ref"),
                    "uid": child.get("uid"),
                    "jid": child.get("jid"),
                    "instanceid": child.get("instanceid") or child.get("instanceId"),
                    "has_pos": "pos" in child or "position" in child,
                    "has_rot": "rot" in child or "rotation" in child,
                    "has_scale": "scale" in child,
                }
            )
    mesh_key_counts = Counter()
    mesh_type_counts = Counter()
    for mesh in scene.get("mesh", []) if isinstance(scene.get("mesh"), list) else []:
        if isinstance(mesh, dict):
            mesh_key_counts.update(mesh.keys())
            mesh_type_counts[str(mesh.get("type") or "unknown")] += 1
    return {
        "file": path.as_posix(),
        "scene_uid": scene.get("uid") if isinstance(scene, dict) else None,
        "furniture_count": len(furniture),
        "room_count": len(scene.get("scene", {}).get("room", [])) if isinstance(scene.get("scene"), dict) else 0,
        "room_child_count": len(room_children(scene)) if isinstance(scene, dict) else 0,
        "link_rule_counts": dict(link_counts.most_common()),
        "child_examples": child_examples,
        "mesh_key_counts": dict(mesh_key_counts.most_common(30)),
        "mesh_type_counts": dict(mesh_type_counts.most_common(30)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-json-dir", type=Path, required=True, help="Directory containing selected scene JSON files.")
    parser.add_argument("--output", type=Path, required=True, help="JSON report path.")
    args = parser.parse_args()
    scenes = [inspect_scene(path) for path in sorted(args.scene_json_dir.glob("*.json"))]
    report = {"schema_version": "selected-scene-structure-report-v1", "scene_count": len(scenes), "scenes": scenes}
    write_json(args.output, report)
    print(f"Wrote selected scene structure report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
