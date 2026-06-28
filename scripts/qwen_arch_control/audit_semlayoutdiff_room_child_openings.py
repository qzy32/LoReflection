
#!/usr/bin/env python3
"""Audit SemLayoutDiff-style room-child Door/Window policy for 3D-FRONT rooms."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from loreflection.qwen_arch_control.raw_3dfront_adapter import collect_room_child_openings_sem_layoutdiff_style
from loreflection.qwen_arch_control.semantic_topdown_renderer import render_architecture_condition_image, render_full_semantic_target_image
from loreflection.semantic_registry import load_registry

MAJOR_ROOM_TOKENS = ("bedroom", "living", "dining", "kitchen", "bath", "study", "library")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def _is_major(room_type: str) -> bool:
    text = str(room_type or "").lower().replace("_", "")
    return any(token in text for token in MAJOR_ROOM_TOKENS)


def _mesh_type_counts(scene: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    for mesh in scene.get("mesh", []) if isinstance(scene.get("mesh"), list) else []:
        if isinstance(mesh, dict):
            typ = str(mesh.get("type") or "")
            if typ in {"Door", "Window"}:
                counts[typ.lower()] += 1
    return dict(counts)


def _room(scene: dict[str, Any], idx: int) -> dict[str, Any] | None:
    rooms = scene.get("scene", {}).get("room") or scene.get("scene", {}).get("rooms") or []
    if isinstance(rooms, list) and 0 <= idx < len(rooms) and isinstance(rooms[idx], dict):
        return rooms[idx]
    return None


def _room_child_refs(room: dict[str, Any]) -> list[str]:
    return [str(c.get("ref")) for c in room.get("children", []) if isinstance(c, dict)]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({k for r in rows for k in r}) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _human_debug(path: Path, img: Image.Image, title: str) -> None:
    canvas = img.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, canvas.width - 1, canvas.height - 1], outline=(255, 0, 255), width=2)
    draw.text((5, 5), f"NOT_FOR_QWEN {title}", fill=(255, 0, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def _render_review(sample_dir: Path, dataset_root: Path, base_layout_root: Path, row: dict[str, str], arch: dict[str, Any], scene: dict[str, Any], room: dict[str, Any], registry) -> dict[str, Any]:
    sample_id = row["sample_id"]
    anchors = collect_room_child_openings_sem_layoutdiff_style(scene, room, assigned_room_id=sample_id)
    new_arch = json.loads(json.dumps(arch))
    new_arch["anchors"] = anchors
    new_arch["opening_source_policy"] = "semlayoutdiff_room_children_only"
    new_arch["door_anchor_count"] = sum(1 for a in anchors if a["anchor_type"] == "door")
    new_arch["window_anchor_count"] = sum(1 for a in anchors if a["anchor_type"] == "window")
    new_arch["native_room_child_door_count"] = new_arch["door_anchor_count"]
    new_arch["native_room_child_window_count"] = new_arch["window_anchor_count"]
    new_arch["has_room_child_door"] = new_arch["door_anchor_count"] > 0
    new_arch["has_room_child_window"] = new_arch["window_anchor_count"] > 0

    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "raw_room_children_refs.json").write_text(json.dumps(_room_child_refs(room), indent=2, ensure_ascii=False), encoding="utf-8")
    (sample_dir / "raw_scene_mesh_door_window_summary.json").write_text(json.dumps(_mesh_type_counts(scene), indent=2, ensure_ascii=False), encoding="utf-8")
    (sample_dir / "architecture_room_child_only.json").write_text(json.dumps(new_arch, indent=2, ensure_ascii=False), encoding="utf-8")
    _copy_if_exists(dataset_root / row.get("context_image", ""), sample_dir / "old_qwen_input.png")
    qwen_input, context_report = render_architecture_condition_image(new_arch, sample_dir / "qwen_input_room_child_only.png", registry=registry)
    layout_path = base_layout_root / "meta" / f"{sample_id}_layout.json"
    target_report: dict[str, Any] = {}
    if layout_path.exists():
        _, target_report = render_full_semantic_target_image(new_arch, _read_json(layout_path), sample_dir / "target_full_semantic_room_child_only.png", registry=registry)
    _human_debug(sample_dir / "human_debug_room_child_refs_NOT_FOR_QWEN.png", qwen_input, "room-child openings")
    render_debug = {"context_report": context_report, "target_report": target_report}
    (sample_dir / "render_debug.json").write_text(json.dumps(render_debug, indent=2, ensure_ascii=False), encoding="utf-8")
    door_pixels = int((context_report.get("anchor_pixel_counts") or {}).get("door") or 0)
    window_pixels = int((context_report.get("anchor_pixel_counts") or {}).get("window") or 0)
    scene_counts = _mesh_type_counts(scene)
    scene_global_ignored = scene_counts.get("door", 0) > new_arch["door_anchor_count"]
    drop_reason = "" if new_arch["door_anchor_count"] > 0 else "drop_no_room_child_door_anchor"
    md = f"""# SemLayoutDiff Room-child Opening Review

sample_id: `{sample_id}`

![qwen input](qwen_input_room_child_only.png)
![target full semantic](target_full_semantic_room_child_only.png)
![human debug](human_debug_room_child_refs_NOT_FOR_QWEN.png)

## Counts
- scene global door count: `{scene_counts.get('door', 0)}`
- scene global window count: `{scene_counts.get('window', 0)}`
- room.children door refs: `{new_arch['door_anchor_count']}`
- room.children window refs: `{new_arch['window_anchor_count']}`
- qwen_input door pixels: `{door_pixels}`
- qwen_input window pixels: `{window_pixels}`
- scene global door ignored: `{scene_global_ignored}`
- drop reason: `{drop_reason}`

## Policy
Only Door/Window meshes referenced by this room's `children` list count as room openings. Scene-global Door/Window meshes are ignored when not referenced by this room.
"""
    (sample_dir / "review.md").write_text(md, encoding="utf-8")
    return {"sample_id": sample_id, "door_pixels": door_pixels, "window_pixels": window_pixels, "drop_reason": drop_reason}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", default="data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled")
    ap.add_argument("--base-layout-root", default="data/loreflection_qwen_arch_control_full_metric_v2")
    ap.add_argument("--out", default="reports/semlayoutdiff_room_child_opening_cleanup")
    args = ap.parse_args()
    dataset_root = Path(args.dataset_root)
    base_layout_root = Path(args.base_layout_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((dataset_root / "metadata.csv").open(encoding="utf-8", newline="")))
    scene_cache: dict[str, dict[str, Any]] = {}
    registry = load_registry()
    coverage = []
    dropped = []
    reviews: dict[str, dict[str, Any] | None] = {"has_door": None, "has_window": None, "scene_global_ignored": None, "drop_major": None}

    for row in rows:
        sample_id = row["sample_id"]
        arch_path = dataset_root / "meta" / f"{sample_id}_architecture.json"
        if not arch_path.exists():
            continue
        arch = _read_json(arch_path)
        source_scene = Path((arch.get("source") or {}).get("source_scene_json") or "")
        room_index = int((arch.get("source") or {}).get("room_index") or sample_id.rsplit("_room_", 1)[-1])
        scene_key = str(source_scene)
        if scene_key not in scene_cache:
            scene_cache[scene_key] = _read_json(source_scene)
        scene = scene_cache[scene_key]
        room = _room(scene, room_index)
        if room is None:
            continue
        anchors = collect_room_child_openings_sem_layoutdiff_style(scene, room, assigned_room_id=sample_id)
        door_count = sum(1 for a in anchors if a["anchor_type"] == "door")
        window_count = sum(1 for a in anchors if a["anchor_type"] == "window")
        scene_counts = _mesh_type_counts(scene)
        room_type = str(arch.get("room_type") or "")
        major = _is_major(room_type)
        drop_reason = "drop_no_room_child_door_anchor" if door_count == 0 else ""
        rec = {
            "sample_id": sample_id,
            "room_type": room_type,
            "is_major_room": major,
            "door_anchor_count": door_count,
            "window_anchor_count": window_count,
            "native_room_child_door_count": door_count,
            "native_room_child_window_count": window_count,
            "has_room_child_door": door_count > 0,
            "has_room_child_window": window_count > 0,
            "scene_global_door_count": scene_counts.get("door", 0),
            "scene_global_window_count": scene_counts.get("window", 0),
            "scene_global_door_ignored": scene_counts.get("door", 0) > door_count,
            "opening_source_policy": "semlayoutdiff_room_children_only",
            "training_gate_status": "pass" if door_count > 0 else "drop",
            "drop_reason": drop_reason,
            "source_scene_json": str(source_scene),
        }
        coverage.append(rec)
        if drop_reason:
            dropped.append(rec)
        payload = {"row": row, "arch": arch, "scene": scene, "room": room, "coverage": rec}
        if door_count > 0 and reviews["has_door"] is None:
            reviews["has_door"] = payload
        if window_count > 0 and reviews["has_window"] is None:
            reviews["has_window"] = payload
        if scene_counts.get("door", 0) > 0 and door_count == 0 and reviews["scene_global_ignored"] is None:
            reviews["scene_global_ignored"] = payload
        if major and door_count == 0 and reviews["drop_major"] is None:
            reviews["drop_major"] = payload

    _write_csv(out / "room_child_opening_coverage.csv", coverage)
    _write_csv(out / "drop_no_room_child_door_rooms.csv", dropped)
    review_paths = []
    seen = set()
    for label, payload in reviews.items():
        if not payload:
            continue
        sid = payload["row"]["sample_id"]
        if sid in seen:
            continue
        seen.add(sid)
        sample_dir = out / "review_samples" / f"{label}_{sid}"
        _render_review(sample_dir, dataset_root, base_layout_root, payload["row"], payload["arch"], payload["scene"], payload["room"], registry)
        review_paths.append(str(sample_dir))

    major_rows = [r for r in coverage if r["is_major_room"]]
    summary = {
        "total_rooms_scanned": len(coverage),
        "rooms_with_room_child_door": sum(1 for r in coverage if r["has_room_child_door"]),
        "rooms_with_room_child_window": sum(1 for r in coverage if r["has_room_child_window"]),
        "major_rooms_scanned": len(major_rows),
        "major_rooms_with_room_child_door": sum(1 for r in major_rows if r["has_room_child_door"]),
        "major_rooms_without_room_child_door": sum(1 for r in major_rows if not r["has_room_child_door"]),
        "drop_no_room_child_door_count": len(dropped),
        "opening_source_policy": "semlayoutdiff_room_children_only",
        "scene_global_door_not_counted_unless_room_child_ref": True,
        "historical_scene_level_assignment_count_not_current_policy": "15457 rooms in the older scene-level assignment report was historical and is not the current target",
        "review_samples": review_paths,
        "training_started": False,
        "full_data_regenerated": False,
    }
    (out / "semlayoutdiff_room_child_opening_cleanup.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    md = f"""# SemLayoutDiff Room-child Opening Cleanup

## Policy
Current LoReflection opening policy is `semlayoutdiff_room_children_only`:

- 3D-FRONT JSON is scene-level.
- The adapter may read complete `data['mesh']`.
- A room only has a door/window if that room's `scene.room[].children` references a `Door` / `Window` mesh.
- Scene-global Door/Window meshes not referenced by the current room are ignored.
- No scene-level geometry recovery is used.
- No fabricated door is allowed.

## Counts
- total_rooms_scanned: `{summary['total_rooms_scanned']}`
- rooms_with_room_child_door: `{summary['rooms_with_room_child_door']}`
- rooms_with_room_child_window: `{summary['rooms_with_room_child_window']}`
- major_rooms_scanned: `{summary['major_rooms_scanned']}`
- major_rooms_with_room_child_door: `{summary['major_rooms_with_room_child_door']}`
- major_rooms_without_room_child_door: `{summary['major_rooms_without_room_child_door']}`
- drop_no_room_child_door_count: `{summary['drop_no_room_child_door_count']}`

## Historical Comparison
Older scene-level assignment figures are historical only and are not used by current mainline logic.

## Recommendation
Next full_semantic_compiled_main regeneration should filter with `has_room_child_door == true`. Do not train on the existing unfiltered metadata.
"""
    (out / "SEMLAYOUTDIFF_ROOM_CHILD_OPENING_CLEANUP.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
