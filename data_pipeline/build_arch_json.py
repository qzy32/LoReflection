#!/usr/bin/env python
"""Build a toy Architecture JSON placeholder without requiring 3D-FRONT."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_architecture(architecture_id: str, room_type: str, width_m: float, depth_m: float) -> dict:
    return {
        "schema_version": "architecture-v1",
        "architecture_id": architecture_id,
        "room_type": room_type,
        "coordinate_system": {
            "layout_plane": "xz",
            "vertical_axis": "y",
            "unit": "meter",
            "orientation_convention": {"zero_degree_axis": "+x", "positive_direction": "counter_clockwise", "unit": "degree"},
        },
        "coordinate_transforms": [
            {"transform_id": "xz_to_image_001", "from": "world_xz_meter", "to": "image_pixel", "image_size_px": [512, 512]}
        ],
        "boundary": {"polygon_m": [[0, 0], [width_m, 0], [width_m, depth_m], [0, depth_m]]},
        "anchors": [
            {"anchor_id": "wall_south", "anchor_type": "wall", "segment_m": [[0, 0], [width_m, 0]]},
            {"anchor_id": "door_001", "anchor_type": "door", "bbox_m": [width_m * 0.42, 0, width_m * 0.58, 0.18], "swing": "inward"},
            {"anchor_id": "window_001", "anchor_type": "window", "bbox_m": [width_m * 0.32, depth_m - 0.15, width_m * 0.68, depth_m]},
            {"anchor_id": "door_001_clearance", "anchor_type": "clearance", "polygon_m": [[width_m * 0.36, 0], [width_m * 0.64, 0], [width_m * 0.64, 1.0], [width_m * 0.36, 1.0]]},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Output Architecture JSON.")
    parser.add_argument("--architecture-id", default="toy_arch_001", help="Architecture id.")
    parser.add_argument("--room-type", default="bedroom", help="Room type.")
    parser.add_argument("--width-m", type=float, default=4.2, help="Room width in meters.")
    parser.add_argument("--depth-m", type=float, default=3.6, help="Room depth in meters.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_architecture(args.architecture_id, args.room_type, args.width_m, args.depth_m), indent=2), encoding="utf-8")
    print(f"Wrote architecture JSON to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

