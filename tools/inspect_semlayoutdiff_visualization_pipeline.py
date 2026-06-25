#!/usr/bin/env python3
"""Inspect SemLayoutDiff visualization sources without running rendering."""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
from pathlib import Path
from typing import Any


KEYWORDS = re.compile(
    r"orthographic|top.?down|label_map|color_palette|semantic_color|include_arch|door|window|wall|floor|room_mask|"
    r"architecture|imshow|savefig|imwrite|Image\.fromarray|Rectangle|Polygon|legend|Patch|Line2D|zorder|alpha|"
    r"padding|crop|resize",
    re.IGNORECASE,
)

REQUIRED_FILES = [
    "preprocess/README.md",
    "preprocess/semlayout/render_dataset_improved_mat.py",
    "preprocess/semlayout/multi_render.py",
    "preprocess/semlayout/visualization/front3d/data_process_front3d.py",
    "preprocess/scripts/data_processor.py",
    "preprocess/scripts/data_to_npy.py",
    "preprocess/metadata/color_palette.json",
    "preprocess/metadata/render_orthographic.json",
    "preprocess/metadata/semantic_color_index_bedroom.csv",
    "preprocess/metadata/semantic_color_index_livingdiningroom.csv",
    "preprocess/metadata/unified_idx_to_generic_label.json",
    "preprocess/metadata/unified_idx_to_generic_label_w_arch.json",
]


def read_text(path: Path, max_chars: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def png_size(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()[:32]
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height = struct.unpack(">II", data[16:24])
            return {"path": str(path), "width": width, "height": height, "format": "png"}
    except OSError as exc:
        return {"path": str(path), "error": repr(exc)}
    return {"path": str(path), "format": "unknown"}


def grep_file(path: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    text = read_text(path)
    for idx, line in enumerate(text.splitlines(), start=1):
        if KEYWORDS.search(line):
            stripped = line.strip()
            if stripped:
                hits.append({"line": idx, "text": stripped[:220]})
        if len(hits) >= 40:
            break
    return hits


def inspect_csv(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return result
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            rows = list(csv.reader(f))
        result["row_count"] = len(rows)
        result["head"] = rows[:8]
    except Exception as exc:  # noqa: BLE001 - report-only scanner
        result["error"] = repr(exc)
    return result


def inspect_json(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return result
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        result["top_type"] = type(data).__name__
        if isinstance(data, dict):
            result["top_keys"] = list(data.keys())[:60]
            result["sample"] = {k: data[k] for k in list(data.keys())[:5]}
        elif isinstance(data, list):
            result["length"] = len(data)
            result["sample"] = data[:5]
    except Exception as exc:  # noqa: BLE001 - report-only scanner
        result["error"] = repr(exc)
    return result


def collect_source_evidence(root: Path) -> dict[str, Any]:
    required = []
    for rel in REQUIRED_FILES:
        path = root / rel
        required.append(
            {
                "relative_path": rel,
                "exists": path.exists(),
                "keyword_hits": grep_file(path) if path.exists() and path.suffix.lower() in {".py", ".md", ".yaml", ".yml"} else [],
            }
        )

    front3d_dir = root / "preprocess" / "semlayout" / "visualization" / "front3d"
    front3d_files = []
    if front3d_dir.exists():
        for path in sorted(front3d_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".py", ".md", ".json", ".yaml", ".yml"}:
                front3d_files.append(
                    {
                        "relative_path": str(path.relative_to(root)),
                        "keyword_hits": grep_file(path),
                    }
                )

    metadata = []
    metadata_dir = root / "preprocess" / "metadata"
    if metadata_dir.exists():
        for path in sorted(metadata_dir.glob("*")):
            if path.suffix.lower() == ".json":
                metadata.append(inspect_json(path))
            elif path.suffix.lower() == ".csv":
                metadata.append(inspect_csv(path))

    grep_hits = []
    preprocess = root / "preprocess"
    if preprocess.exists():
        for path in sorted(preprocess.rglob("*")):
            if not path.is_file() or path.suffix.lower() in {".pkl", ".npy", ".npz", ".png", ".jpg", ".jpeg"}:
                continue
            if path.stat().st_size > 1_000_000:
                continue
            hits = grep_file(path)
            if hits:
                grep_hits.append({"relative_path": str(path.relative_to(root)), "hits": hits[:12]})
            if len(grep_hits) >= 80:
                break

    return {
        "required_files": required,
        "front3d_visualization_files": front3d_files[:80],
        "metadata_files": metadata,
        "keyword_evidence": grep_hits,
    }


def collect_processed_evidence(root: Path) -> dict[str, Any]:
    names = [
        "Updated_Bottom_label_map.png",
        "Updated_Bottom_color.png",
        "Updated_Bottom_inst_anno.json",
    ]
    found: dict[str, list[dict[str, Any]]] = {name: [] for name in names}
    for name in names:
        for path in sorted(root.rglob(name)):
            item = png_size(path) if path.suffix.lower() == ".png" else inspect_json(path)
            item["relative_path"] = str(path.relative_to(root))
            found[name].append(item)
            if len(found[name]) >= 10:
                break
    related = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        low = path.name.lower()
        if any(token in low for token in ["label_map", "color", "inst_anno", "semantic", "architecture", "room_mask"]):
            related.append(str(path.relative_to(root)))
        if len(related) >= 80:
            break
    return {"named_outputs": found, "related_candidates": related}


def infer_policy(evidence: dict[str, Any]) -> dict[str, Any]:
    flat = json.dumps(evidence, ensure_ascii=False).lower()
    legend_hits = [item for item in evidence.get("keyword_evidence", []) if "legend" in json.dumps(item).lower()]
    return {
        "raw_topdown_render_entry": "preprocess/semlayout/render_dataset_improved_mat.py and preprocess/semlayout/multi_render.py if present",
        "semantic_architecture_extraction_entry": "preprocess/scripts/data_processor.py, preprocess/scripts/data_to_npy.py, and front3d visualization helpers if present",
        "orthographic_camera_policy": "hard_source_evidence_found" if "orthographic" in flat else "unknown",
        "room_framing_padding_policy": "hard_source_evidence_found" if any(k in flat for k in ["padding", "crop", "resize"]) else "unknown",
        "category_to_color_policy": "metadata color palette / semantic_color_index files" if "semantic_color" in flat or "color_palette" in flat else "unknown",
        "architecture_element_policy": {
            "floor": "mentioned" if "floor" in flat else "unknown",
            "wall_or_boundary": "mentioned" if "wall" in flat or "boundary" in flat else "unknown",
            "door": "mentioned" if "door" in flat else "unknown",
            "window": "mentioned" if "window" in flat else "unknown",
            "include_arch": "mentioned" if "include_arch" in flat else "unknown",
        },
        "verified_builtin_legend_support": bool(legend_hits),
        "legend_note": (
            "Potential legend-related source hits were found; inspect evidence before claiming built-in human-facing legend support."
            if legend_hits
            else "SemLayoutDiff provides palette/color mappings, but no verified built-in human-facing legend generator was found. LoReflection legend is an audit visualization enhancement."
        ),
        "reusable_ideas": [
            "fixed category-to-color mappings",
            "top-down orthographic framing / crop policy",
            "separate semantic label maps from colored human-readable maps",
            "architecture-aware rendering policy when include_arch is available",
        ],
        "non_reusable_ideas": [
            "Do not run Blender/BlenderProc in this audit-only step.",
            "Do not treat processed SemLayoutDiff PNGs as LoReflection raw source.",
            "Do not copy project-specific rendering code blindly into the converter.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    policy = report["policy_summary"]
    lines = [
        "# SemLayoutDiff Visualization Reference",
        "",
        "This note records read-only evidence from the local SemLayoutDiff repository. It is a visualization reference, not a converter implementation transplant.",
        "",
        "## Evidence Types",
        "- Hard source evidence: files and keyword hits found in SemLayoutDiff source or metadata.",
        "- Existing processed-output evidence: already existing label/color/annotation files found on disk.",
        "- Inference: LoReflection interpretation for audit-view design.",
        "",
        "## Main Findings",
        f"- Raw top-down render entry: `{policy['raw_topdown_render_entry']}`.",
        f"- Semantic / architecture extraction entry: `{policy['semantic_architecture_extraction_entry']}`.",
        f"- Orthographic camera policy: `{policy['orthographic_camera_policy']}`.",
        f"- Room framing / padding policy: `{policy['room_framing_padding_policy']}`.",
        f"- Category-to-color policy: `{policy['category_to_color_policy']}`.",
        f"- Built-in human-facing legend support: `{policy['verified_builtin_legend_support']}`.",
        f"- Legend note: {policy['legend_note']}",
        "",
        "## LoReflection Use",
        "- Reuse palette discipline and top-down audit framing ideas.",
        "- Keep canonical machine-facing images separate from human-facing audit overlays.",
        "- Add LoReflection legends only in `visual_audit_v2`; do not write legends into training label maps.",
        "",
        "## Do Not Reuse Blindly",
    ]
    for item in policy["non_reusable_ideas"]:
        lines.append(f"- {item}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root = args.semlayoutdiff_root
    source_evidence = collect_source_evidence(root)
    processed_evidence = collect_processed_evidence(root)
    report = {
        "report_version": "semlayoutdiff_visualization_reference_v1",
        "semlayoutdiff_root": str(root),
        "hard_source_evidence": source_evidence,
        "existing_processed_output_evidence": processed_evidence,
        "policy_summary": infer_policy({**source_evidence, **processed_evidence}),
        "inference": {
            "loreflection_visual_audit_v2": "Use SemLayoutDiff-style top-down separation and palette discipline, but add audit-only legends and high-contrast architecture markers.",
            "canonical_outputs_should_change": False,
        },
    }
    write_json(args.output, report)
    write_markdown(args.markdown, report)
    if args.verbose:
        print(json.dumps(report["policy_summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
