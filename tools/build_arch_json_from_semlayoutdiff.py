#!/usr/bin/env python
"""Convert a toy SemLayoutDiff/3D-FRONT-like room metadata JSON to LoReflection Architecture JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_image_size(text: str) -> list[int]:
    """Parse image size as N or WIDTHxHEIGHT."""
    if "x" in text.lower():
        left, right = text.lower().split("x", 1)
        return [int(left), int(right)]
    size = int(text)
    return [size, size]


def door_clearance_from_bbox(bbox: list[float], depth_m: float) -> list[list[float]]:
    """Create a simple inward clearance polygon for a door bbox in toy coordinates."""
    x0, y0, x1, y1 = bbox
    clearance_depth = min(1.0, max(depth_m * 0.25, 0.5))
    return [[x0, y0], [x1, y0], [x1, y0 + clearance_depth], [x0, y0 + clearance_depth]]


def convert_toy_room_meta(room_meta: dict, architecture_id: str, room_type: str | None, image_size_px: list[int]) -> dict:
    """Build Architecture JSON from the supported toy room_meta format.

    TODO(server): map real SemLayoutDiff/3D-FRONT room fields after inspecting the
    upstream preprocessed pickle/npy/json outputs. Do not infer real field names
    from this toy adapter.
    """
    boundary = room_meta["boundary"]
    xs = [point[0] for point in boundary]
    ys = [point[1] for point in boundary]
    depth_m = max(ys) - min(ys)
    anchors: list[dict] = []

    for index, door in enumerate(room_meta.get("doors", []), start=1):
        door_id = door.get("anchor_id", f"door_{index:03d}")
        bbox = door["bbox"]
        anchors.append({"anchor_id": door_id, "anchor_type": "door", "bbox_m": bbox, "swing": door.get("swing", "unknown")})
        anchors.append(
            {
                "anchor_id": f"{door_id}_clearance",
                "anchor_type": "clearance",
                "polygon_m": door.get("clearance_polygon", door_clearance_from_bbox(bbox, depth_m)),
            }
        )

    for index, window in enumerate(room_meta.get("windows", []), start=1):
        window_id = window.get("anchor_id", f"window_{index:03d}")
        anchors.append({"anchor_id": window_id, "anchor_type": "window", "bbox_m": window["bbox"]})

    for index in range(len(boundary)):
        p0 = boundary[index]
        p1 = boundary[(index + 1) % len(boundary)]
        anchors.append({"anchor_id": f"wall_{index + 1:03d}", "anchor_type": "wall", "segment_m": [p0, p1]})

    return {
        "schema_version": "architecture-v1",
        "architecture_id": architecture_id,
        "room_type": room_type or room_meta.get("room_type", "room"),
        "image_size_px": image_size_px,
        "coordinate_system": {
            "layout_plane": "xz",
            "vertical_axis": "y",
            "unit": "meter",
            "orientation_convention": {"zero_degree_axis": "+x", "positive_direction": "counter_clockwise", "unit": "degree"},
        },
        "coordinate_transforms": [
            {
                "transform_id": "xz_to_image_001",
                "from": "world_xz_meter",
                "to": "image_pixel",
                "image_size_px": image_size_px,
                "note": "Toy adapter uses render_arch_condition.py scaling; server adapter should record the real SemLayoutDiff transform.",
            }
        ],
        "boundary": {"polygon_m": boundary},
        "anchors": anchors,
        "source": {"adapter": "SemLayoutDiff toy adapter", "source_format": "toy_room_meta_json"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Toy room_meta.json or future SemLayoutDiff room metadata JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output LoReflection Architecture JSON.")
    parser.add_argument("--room-type", default=None, help="Override room type.")
    parser.add_argument("--architecture-id", default=None, help="Architecture id. Defaults to input directory name.")
    parser.add_argument("--image-size", default="1024", help="Output image size as N or WIDTHxHEIGHT.")
    args = parser.parse_args()

    room_meta = load_json(args.input)
    architecture_id = args.architecture_id or args.input.parent.name
    architecture = convert_toy_room_meta(room_meta, architecture_id, args.room_type, parse_image_size(args.image_size))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(architecture, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote LoReflection Architecture JSON to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

