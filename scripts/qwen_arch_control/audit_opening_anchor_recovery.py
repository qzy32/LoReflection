#!/usr/bin/env python3
"""Audit scene-level opening recovery without regenerating a dataset."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from loreflection.qwen_arch_control.opening_anchor_recovery import (
    collect_scene_opening_candidates,
    opening_assignment_debug,
    recover_opening_anchors_for_room,
)
from loreflection.qwen_arch_control.semantic_topdown_renderer import (
    render_architecture_condition_image,
    render_full_semantic_target_image,
)
from loreflection.semantic_registry import load_registry

MAJOR_ROOM_TOKENS = ("bedroom", "living", "dining", "kitchen", "bath", "study", "library")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def _is_major(room_type: str) -> bool:
    text = str(room_type or "").lower().replace("_", "")
    return any(token in text for token in MAJOR_ROOM_TOKENS)


def _anchor_count(arch: dict[str, Any], kind: str) -> int:
    return sum(1 for anchor in arch.get("anchors", []) or [] if str(anchor.get("anchor_type", "")).lower() == kind)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row}) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _draw_human_debug(path: Path, arch: dict[str, Any], assigned: list[dict[str, Any]]) -> None:
    image, _ = render_architecture_condition_image(arch)
    canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    draw.text((6, 6), "NOT_FOR_QWEN opening assignment", fill=(255, 0, 255))
    draw.rectangle([0, 0, canvas.width - 1, canvas.height - 1], outline=(255, 0, 255), width=2)
    for anchor in assigned:
        bbox = anchor.get("bbox_px")
        if bbox:
            xy = [int(v) for v in bbox]
            draw.rectangle(xy, outline=(255, 0, 255), width=3)
            draw.text((xy[0], max(0, xy[1] - 12)), str(anchor.get("anchor_type")), fill=(255, 0, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def _review_markdown(sample_id: str, coverage: dict[str, Any], door_pixels: int, window_pixels: int) -> str:
    return f"""# Opening Anchor Recovery Review

sample_id: `{sample_id}`

## Status
- room_type: `{coverage.get('room_type')}`
- door before: `{coverage.get('door_anchor_count_before')}`
- window before: `{coverage.get('window_anchor_count_before')}`
- door after: `{coverage.get('door_anchor_count_after_recovery')}`
- window after: `{coverage.get('window_anchor_count_after_recovery')}`
- new_qwen_input door pixels: `{door_pixels}`
- new_qwen_input window pixels: `{window_pixels}`
- training_gate_status: `{coverage.get('training_gate_status')}`

## Images
![old qwen input](old_qwen_input.png)
![new qwen input](new_qwen_input_with_recovered_door.png)
![new target](new_target_full_semantic.png)
![human debug](human_debug_opening_assignment_NOT_FOR_QWEN.png)

Recovered anchors are assigned from explicit scene-level Door/Window candidates only when they are near the room floor boundary. No random or fabricated door is inserted.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled")
    parser.add_argument("--base-layout-root", default="data/loreflection_qwen_arch_control_full_metric_v2")
    parser.add_argument("--out", default="reports/opening_anchor_recovery_audit")
    parser.add_argument("--max-rows", type=int, default=0)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    base_layout_root = Path(args.base_layout_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader((dataset_root / "metadata.csv").open(newline="", encoding="utf-8")))
    if args.max_rows:
        rows = rows[: args.max_rows]

    registry = load_registry()
    scene_cache: dict[str, dict[str, Any]] = {}
    candidate_cache: dict[str, list[dict[str, Any]]] = {}
    coverage_rows: list[dict[str, Any]] = []
    recovered_rows: list[dict[str, Any]] = []
    no_recoverable_rows: list[dict[str, Any]] = []
    boundary_rows: list[dict[str, Any]] = []
    reviews: dict[str, dict[str, Any] | None] = {
        "recovered_bedroom": None,
        "recovered_other_major": None,
        "already_has_door": None,
        "no_recoverable": None,
        "has_window": None,
    }
    extra_reviews: list[tuple[str, dict[str, Any]]] = []

    for row in rows:
        sample_id = row["sample_id"]
        arch_path = dataset_root / "meta" / f"{sample_id}_architecture.json"
        if not arch_path.exists():
            continue
        arch = _read_json(arch_path)
        source_scene = Path((arch.get("source") or {}).get("source_scene_json") or "")
        if not source_scene.exists():
            continue
        scene_key = str(source_scene)
        if scene_key not in scene_cache:
            scene_cache[scene_key] = _read_json(source_scene)
            candidate_cache[scene_key] = collect_scene_opening_candidates(scene_cache[scene_key], {})
        candidates = candidate_cache[scene_key]
        boundary = (arch.get("boundary") or {}).get("polygon_m") or []
        room_type = str(arch.get("room_type") or "")
        before_door = _anchor_count(arch, "door")
        before_window = _anchor_count(arch, "window")
        recovered = recover_opening_anchors_for_room(
            candidates,
            boundary,
            assigned_room_id=sample_id,
            existing_anchors=arch.get("anchors", []) or [],
            metric_transform=arch.get("metric_transform"),
            image_size=int((arch.get("image_size_px") or [256])[0]),
        )
        recovered_door = sum(1 for anchor in recovered if anchor.get("anchor_type") == "door")
        recovered_window = sum(1 for anchor in recovered if anchor.get("anchor_type") == "window")
        after_door = before_door + recovered_door
        after_window = before_window + recovered_window
        is_major = _is_major(room_type)
        gate = "pass" if (not is_major or after_door >= 1) else "drop_no_recoverable_door_anchor"
        coverage = {
            "sample_id": sample_id,
            "room_type": room_type,
            "is_major_room": is_major,
            "door_anchor_count_before": before_door,
            "window_anchor_count_before": before_window,
            "door_anchor_count_after_recovery": after_door,
            "window_anchor_count_after_recovery": after_window,
            "door_recovered": recovered_door > 0,
            "window_recovered": recovered_window > 0,
            "door_recovery_source": ";".join(sorted({str(anchor.get("source")) for anchor in recovered if anchor.get("anchor_type") == "door"})),
            "boundary_source": (arch.get("boundary") or {}).get("boundary_source") or (arch.get("boundary") or {}).get("source"),
            "boundary_is_bbox_fallback": ((arch.get("boundary") or {}).get("boundary_source") == "furniture_extent_fallback"),
            "training_gate_status": gate,
            "source_scene_json": str(source_scene),
        }
        coverage_rows.append(coverage)
        boundary_rows.append({k: coverage[k] for k in ("sample_id", "room_type", "boundary_source", "boundary_is_bbox_fallback", "source_scene_json")})
        for anchor in recovered:
            recovered_rows.append({
                "sample_id": sample_id,
                "anchor_type": anchor.get("anchor_type"),
                "source": anchor.get("source"),
                "source_id": anchor.get("source_id"),
                "confidence": anchor.get("confidence"),
                "distance_to_room_boundary_m": anchor.get("distance_to_room_boundary_m"),
                "assignment_method": anchor.get("assignment_method"),
            })
        if gate != "pass":
            no_recoverable_rows.append(coverage)

        payload = {"row": row, "arch": arch, "recovered": recovered, "coverage": coverage, "candidates": candidates}
        if recovered_door and "bed" in room_type.lower() and reviews["recovered_bedroom"] is None:
            reviews["recovered_bedroom"] = payload
        if recovered_door and is_major and "bed" not in room_type.lower() and reviews["recovered_other_major"] is None:
            reviews["recovered_other_major"] = payload
        if before_door and reviews["already_has_door"] is None:
            reviews["already_has_door"] = payload
        if gate != "pass" and reviews["no_recoverable"] is None:
            reviews["no_recoverable"] = payload
        if after_window and reviews["has_window"] is None:
            reviews["has_window"] = payload
        if recovered_door and len(extra_reviews) < 12:
            extra_reviews.append((f"extra_recovered_{len(extra_reviews) + 1:02d}", payload))

    _write_csv(out / "room_opening_coverage.csv", coverage_rows)
    _write_csv(out / "recovered_opening_candidates.csv", recovered_rows)
    _write_csv(out / "no_recoverable_door_rooms.csv", no_recoverable_rows)
    _write_csv(out / "boundary_source_audit.csv", boundary_rows)

    review_paths: list[str] = []
    seen: set[str] = set()
    ordered_reviews = list(reviews.items()) + extra_reviews
    for label, payload in ordered_reviews:
        if not payload:
            continue
        row = payload["row"]
        sample_id = row["sample_id"]
        if sample_id in seen:
            continue
        if len(seen) >= 5:
            break
        seen.add(sample_id)
        sample_dir = out / "review_samples" / f"{label}_{sample_id}"
        sample_dir.mkdir(parents=True, exist_ok=True)
        arch = payload["arch"]
        new_arch = json.loads(json.dumps(arch))
        new_arch["anchors"] = (new_arch.get("anchors") or []) + payload["recovered"]
        (sample_dir / "old_architecture.json").write_text(json.dumps(arch, indent=2, ensure_ascii=False), encoding="utf-8")
        (sample_dir / "new_architecture_with_recovered_openings.json").write_text(json.dumps(new_arch, indent=2, ensure_ascii=False), encoding="utf-8")
        (sample_dir / "raw_3dfront_scene_ref.txt").write_text(str((arch.get("source") or {}).get("source_scene_json")), encoding="utf-8")
        (sample_dir / "opening_candidates.json").write_text(json.dumps(payload["candidates"], indent=2, ensure_ascii=False), encoding="utf-8")
        assignment_debug = [opening_assignment_debug(candidate, (arch.get("boundary") or {}).get("polygon_m") or []) for candidate in payload["candidates"]]
        (sample_dir / "room_assignment_debug.json").write_text(json.dumps(assignment_debug, indent=2, ensure_ascii=False), encoding="utf-8")
        _copy_if_exists(dataset_root / row.get("context_image", ""), sample_dir / "old_qwen_input.png")
        _, report = render_architecture_condition_image(new_arch, sample_dir / "new_qwen_input_with_recovered_door.png", registry=registry)
        layout_path = base_layout_root / "meta" / f"{sample_id}_layout.json"
        if layout_path.exists():
            layout = _read_json(layout_path)
            render_full_semantic_target_image(new_arch, layout, sample_dir / "new_target_full_semantic.png", registry=registry)
        _draw_human_debug(sample_dir / "human_debug_opening_assignment_NOT_FOR_QWEN.png", new_arch, payload["recovered"])
        door_pixels = int((report.get("anchor_pixel_counts") or {}).get("door") or 0)
        window_pixels = int((report.get("anchor_pixel_counts") or {}).get("window") or 0)
        (sample_dir / "review.md").write_text(_review_markdown(sample_id, payload["coverage"], door_pixels, window_pixels), encoding="utf-8")
        review_paths.append(str(sample_dir))

    total = len(coverage_rows)
    major_rows = [row for row in coverage_rows if row["is_major_room"]]
    summary = {
        "total_rooms_scanned": total,
        "rooms_with_door_before_recovery": sum(1 for row in coverage_rows if row["door_anchor_count_before"] > 0),
        "rooms_with_door_after_recovery": sum(1 for row in coverage_rows if row["door_anchor_count_after_recovery"] > 0),
        "rooms_with_window_before_recovery": sum(1 for row in coverage_rows if row["window_anchor_count_before"] > 0),
        "rooms_with_window_after_recovery": sum(1 for row in coverage_rows if row["window_anchor_count_after_recovery"] > 0),
        "major_rooms_scanned": len(major_rows),
        "major_rooms_with_door_before_recovery": sum(1 for row in major_rows if row["door_anchor_count_before"] > 0),
        "major_rooms_with_door_after_recovery": sum(1 for row in major_rows if row["door_anchor_count_after_recovery"] > 0),
        "major_rooms_with_window_before_recovery": sum(1 for row in major_rows if row["window_anchor_count_before"] > 0),
        "major_rooms_with_window_after_recovery": sum(1 for row in major_rows if row["window_anchor_count_after_recovery"] > 0),
        "major_rooms_still_without_recoverable_door": sum(1 for row in major_rows if row["door_anchor_count_after_recovery"] < 1),
        "rooms_still_without_recoverable_door": sum(1 for row in coverage_rows if row["door_anchor_count_after_recovery"] < 1),
        "recovery_source_distribution": dict(Counter(row.get("source") for row in recovered_rows)),
        "boundary_source_distribution": dict(Counter(row.get("boundary_source") for row in boundary_rows)),
        "bbox_fallback_boundary_rate": (sum(1 for row in boundary_rows if str(row.get("boundary_is_bbox_fallback")) == "True") / total) if total else None,
        "false_positive_prevention_rules": [
            "wardrobe/cabinet/drawer/shower/appliance door text is excluded",
            "candidate must be explicit Door/Window mesh or structural door/window furniture",
            "candidate must be near room boundary",
            "no random or fabricated openings",
        ],
        "review_samples": review_paths,
        "training_recommendation": "do_not_train_until_full_semantic_compiled_main_is_regenerated_with_recovered_opening_anchors_and no-door major rooms are dropped",
    }
    (out / "opening_anchor_recovery_audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    md = f"""# Opening Anchor Recovery Audit

## Scope
This audit does not regenerate the dataset, overwrite metadata, start training, or fabricate doors/windows. It scans existing full_semantic_compiled_main metadata and tests whether explicit scene-level 3D-FRONT Door/Window candidates can be assigned back to per-room Architecture JSON by boundary proximity.

## Findings
- 3D-FRONT JSON granularity: scene-level house/apartment JSON with multiple `scene.room[]` entries, not one JSON per room.
- Current adapter before this fix primarily used `room.children`; scene-level Door/Window not attached to a room could be missed.
- Rooms scanned: `{summary['total_rooms_scanned']}`
- Rooms with door before recovery: `{summary['rooms_with_door_before_recovery']}`
- Rooms with door after recovery: `{summary['rooms_with_door_after_recovery']}`
- Rooms with window before recovery: `{summary['rooms_with_window_before_recovery']}`
- Rooms with window after recovery: `{summary['rooms_with_window_after_recovery']}`
- Major rooms scanned: `{summary['major_rooms_scanned']}`
- Major rooms with door before recovery: `{summary['major_rooms_with_door_before_recovery']}`
- Major rooms with door after recovery: `{summary['major_rooms_with_door_after_recovery']}`
- Major rooms with window before recovery: `{summary['major_rooms_with_window_before_recovery']}`
- Major rooms with window after recovery: `{summary['major_rooms_with_window_after_recovery']}`
- Major rooms still without recoverable door: `{summary['major_rooms_still_without_recoverable_door']}`
- Boundary source distribution: `{summary['boundary_source_distribution']}`
- Recovery source distribution: `{summary['recovery_source_distribution']}`

## room_05 Explanation
For `36c96aa6-a318-4212-aecc-22a206d7b217_room_05`, the raw scene contains a global Door mesh/furniture, but `room_05` children do not include that Door. The recovery pass only assigns that global Door if it is near the room boundary; it does not fabricate a door.

## Gate Policy
Major room types require at least one door/opening anchor. If no explicit candidate can be recovered, the room should be dropped from Qwen training rather than patched with a fake door.

## Outputs
- `room_opening_coverage.csv`
- `recovered_opening_candidates.csv`
- `no_recoverable_door_rooms.csv`
- `boundary_source_audit.csv`
- `review_samples/`

## Recommendation
Do not train on the old full_semantic_compiled_main package. Next step is to regenerate the full package with recovered opening anchors and drop major rooms that still have no recoverable door.
"""
    (out / "OPENING_ANCHOR_RECOVERY_AUDIT.md").write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
