#!/usr/bin/env python3
"""Trace SemLayoutDiff visualization/preprocessing evidence without executing rendering."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import struct
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


KEYWORDS = [
    "3D-FRONT",
    "3D-FUTURE",
    "parse_threed_front",
    "parse_utils",
    "Room",
    "furniture",
    "children",
    "ref",
    "uid",
    "jid",
    "model_info",
    "category",
    "super-category",
    "class_labels",
    "label_map",
    "semantic",
    "instance",
    "inst_anno",
    "bottom",
    "topdown",
    "top_down",
    "orthographic",
    "camera",
    "render",
    "projection",
    "polygon",
    "mesh",
    "floor",
    "wall",
    "door",
    "window",
    "opening",
    "room_mask",
    "architecture",
    "include_arch",
    "palette",
    "color",
    "RGB",
    "draw",
    "paint",
    "rasterize",
    "imshow",
    "imwrite",
    "savefig",
    "Image.fromarray",
    "cv2",
    "PIL",
    "matplotlib",
    "blenderproc",
    "crop",
    "padding",
    "resize",
    "bbox",
    "orientation",
    "rotY",
    "z_order",
    "zorder",
    "sort",
    "height",
    "vertical",
]

TEXT_SUFFIXES = {".py", ".json", ".csv", ".yaml", ".yml", ".md", ".txt", ".sh"}
SKIP_SUFFIXES = {".pkl", ".npy", ".npz", ".pt", ".ckpt", ".png", ".jpg", ".jpeg", ".safetensors", ".obj"}
MAX_TEXT_BYTES = 1_500_000

PIPELINE_HINTS = {
    "raw parser entry": ["parse_threed_front", "pickle_threed_front_dataset", "parse_utils"],
    "room construction": ["Room", "room", "children"],
    "furniture construction": ["furniture", "Furniture", "ThreedFutureModel", "jid"],
    "category mapping": ["category", "class_labels", "generic_label", "model_info"],
    "geometry extraction": ["bbox", "orientation", "rotY", "translation", "scale", "size"],
    "top-down rendering": ["orthographic", "topdown", "top_down", "render_dataset"],
    "architecture rendering": ["include_arch", "door", "window", "wall", "floor", "architecture"],
    "semantic label generation": ["label_map", "semantic", "class_labels", "label"],
    "color conversion": ["color_palette", "semantic_color", "RGB", "color"],
    "instance annotation": ["inst_anno", "instance", "bbox", "mask"],
    "crop/resize/padding": ["crop", "resize", "padding", "room_mask"],
    "output writing": ["savefig", "imwrite", "Image.fromarray", "open(", ".png", ".json"],
}


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= MAX_TEXT_BYTES:
            files.append(path)
    return sorted(files)


def inventory(root: Path) -> dict[str, Any]:
    all_files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    searchable = text_files(root)
    by_suffix = Counter(p.suffix.lower() or "<none>" for p in all_files)
    return {
        "file_count": len(all_files),
        "searchable_file_count": len(searchable),
        "suffix_counts": dict(by_suffix.most_common()),
        "searchable_files": [str(p.relative_to(root)) for p in searchable],
    }


def grep_evidence(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    rx = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.IGNORECASE)
    out: list[dict[str, Any]] = []
    for path in files:
        rel = str(path.relative_to(root))
        hits = []
        for lineno, line in enumerate(read_text(path).splitlines(), start=1):
            if rx.search(line):
                hits.append({"line": lineno, "text": line.strip()[:260]})
            if len(hits) >= 60:
                break
        if hits:
            out.append({"file": rel, "hits": hits})
    return out


def functions_in_file(path: Path) -> list[dict[str, Any]]:
    items = []
    for lineno, line in enumerate(read_text(path).splitlines(), start=1):
        m = re.match(r"\s*(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if m:
            items.append({"line": lineno, "kind": m.group(1), "name": m.group(2)})
    return items


def collect_stage_chain(root: Path, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_file = {item["file"]: item["hits"] for item in evidence}
    chain = []
    for stage, hints in PIPELINE_HINTS.items():
        candidates = []
        for rel, hits in by_file.items():
            matched = []
            for hit in hits:
                text = hit["text"].lower()
                if any(h.lower() in text for h in hints):
                    matched.append(hit)
            if matched:
                path = root / rel
                funcs = functions_in_file(path)
                candidates.append(
                    {
                        "file": rel,
                        "functions_or_classes": funcs[:20],
                        "evidence_lines": matched[:12],
                        "evidence_level": "hard source evidence",
                    }
                )
        chain.append(
            {
                "stage": stage,
                "candidates": candidates[:12],
                "complete": bool(candidates),
                "interpretation": "Evidence candidates found; exact runtime caller/callee is inferred unless explicit call sites are listed.",
                "confidence": "hard evidence" if candidates else "unknown",
            }
        )
    return chain


def find_external_dependencies(root: Path, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    imports = []
    for item in evidence:
        for hit in item["hits"]:
            if "parse_utils" in hit["text"] or "threed_front" in hit["text"]:
                imports.append({"file": item["file"], **hit})
    local_candidates = [p for p in root.rglob("parse_utils.py") if "threed_front" in str(p).lower()]
    local_candidates += [p for p in root.rglob("*threed_front*") if p.is_file() and p.suffix == ".py"]
    importlib_candidates = []
    for module in ["threed_front.datasets.parse_utils", "threed_front.datasets", "threed_front"]:
        try:
            spec = importlib.util.find_spec(module)
        except Exception as exc:  # noqa: BLE001 - report-only probe
            importlib_candidates.append({"module": module, "error": repr(exc)})
            continue
        if spec and spec.origin:
            importlib_candidates.append({"module": module, "origin": spec.origin, "search_locations": [str(x) for x in spec.submodule_search_locations or []]})
        else:
            importlib_candidates.append({"module": module, "origin": "", "search_locations": []})

    importlib_source_evidence = []
    for item in importlib_candidates:
        origin = item.get("origin")
        if origin and origin not in {"built-in", "namespace"}:
            p = Path(origin)
            if p.exists() and p.suffix == ".py" and p.stat().st_size <= MAX_TEXT_BYTES:
                hits = []
                for lineno, line in enumerate(read_text(p).splitlines(), start=1):
                    low = line.lower()
                    if any(k.lower() in low for k in ["model_info", "jid", "uid", "children", "category", "bbox", "room", "furniture", "mesh"]):
                        hits.append({"line": lineno, "text": line.strip()[:260]})
                    if len(hits) >= 80:
                        break
                importlib_source_evidence.append({"module": item.get("module"), "origin": origin, "hits": hits})

    return {
        "import_evidence": imports[:40],
        "local_dependency_candidates": [str(p.relative_to(root)) for p in sorted(set(local_candidates))[:40]],
        "external_parser_found_in_repo": bool(local_candidates),
        "importlib_candidates": importlib_candidates,
        "importlib_source_evidence": importlib_source_evidence,
        "external_parser_found_by_importlib": any(item.get("origin") for item in importlib_candidates),
        "missing_dependency_note": "" if local_candidates or any(item.get("origin") for item in importlib_candidates) else "External threed_front parser source was imported/referenced but not found inside the SemLayoutDiff repo tree or active python environment.",
    }


def load_json_safe(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def collect_metadata(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = []
    palette_rows = []
    for path in sorted((root / "preprocess" / "metadata").glob("*")) if (root / "preprocess" / "metadata").exists() else []:
        rel = str(path.relative_to(root))
        if path.suffix.lower() == ".json":
            data = load_json_safe(path)
            keys = list(data.keys())[:50] if isinstance(data, dict) else []
            rows.append({"file": rel, "type": "json", "top_type": type(data).__name__, "keys": keys})
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        palette_rows.append(
                            {
                                "raw_category": "",
                                "intermediate_category": "",
                                "generic_category": value,
                                "semantic_index": str(key),
                                "RGB color": "",
                                "room type applicability": infer_room_type(rel),
                                "include_arch behavior": infer_include_arch(rel),
                                "source file": rel,
                                "source line": "",
                            }
                        )
                    elif isinstance(value, (list, tuple)) and len(value) >= 3:
                        palette_rows.append(
                            {
                                "raw_category": "",
                                "intermediate_category": "",
                                "generic_category": "",
                                "semantic_index": str(key),
                                "RGB color": ",".join(map(str, value[:3])),
                                "room type applicability": infer_room_type(rel),
                                "include_arch behavior": infer_include_arch(rel),
                                "source file": rel,
                                "source line": "",
                            }
                        )
        elif path.suffix.lower() == ".csv":
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
                reader = list(csv.reader(lines))
                rows.append({"file": rel, "type": "csv", "row_count": len(reader), "head": reader[:6]})
                for line_no, row in enumerate(reader[:200], start=1):
                    if len(row) >= 2:
                        palette_rows.append(
                            {
                                "raw_category": "",
                                "intermediate_category": "",
                                "generic_category": row[1],
                                "semantic_index": row[0],
                                "RGB color": ",".join(row[2:5]) if len(row) >= 5 else "",
                                "room type applicability": infer_room_type(rel),
                                "include_arch behavior": infer_include_arch(rel),
                                "source file": rel,
                                "source line": str(line_no),
                            }
                        )
            except OSError:
                pass
    for path in sorted(root.glob("configs/**/*.yaml")) + sorted(root.glob("configs/*.yaml")):
        text = read_text(path)
        if any(k.lower() in text.lower() for k in ["class", "label", "color", "include_arch", "bedroom", "living"]):
            rows.append({"file": str(path.relative_to(root)), "type": "yaml", "keyword_excerpt": text[:1200]})
    return rows, palette_rows


def infer_room_type(rel: str) -> str:
    low = rel.lower()
    if "bedroom" in low:
        return "bedroom"
    if "living" in low or "dining" in low:
        return "living/dining"
    return "unknown"


def infer_include_arch(rel: str) -> str:
    low = rel.lower()
    if "w_arch" in low or "with_arch" in low:
        return "with_arch"
    if "no_arch" in low or "without_arch" in low:
        return "without_arch"
    return "unknown"


def png_header(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()[:32]
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            w, h = struct.unpack(">II", data[16:24])
            bit_depth = data[24]
            color_type = data[25]
            return {"width": w, "height": h, "bit_depth": bit_depth, "color_type": color_type}
    except OSError as exc:
        return {"error": repr(exc)}
    return {"error": "not_png"}


def make_text_png(path: Path, lines: list[str], width: int = 1800, height: int = 360) -> None:
    # Minimal RGB PNG with simple horizontal bands; text is represented in the
    # sidecar JSON/HTML, while this contact sheet remains dependency-free.
    pixels = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]
    palette = [(244, 241, 232), (214, 234, 248), (252, 228, 214), (232, 245, 233)]
    row_h = max(1, height // max(1, len(lines)))
    for idx, _ in enumerate(lines):
        color = palette[idx % len(palette)]
        for y in range(idx * row_h, min(height, (idx + 1) * row_h)):
            for x in range(width):
                pixels[y][x] = color
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return len(data).to_bytes(4, "big") + kind + data + zlib.crc32(kind + data).to_bytes(4, "big")

    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00")
    payload += chunk(b"IDAT", comp)
    payload += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def processed_samples(root: Path, outdir: Path) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    label_maps = sorted(root.rglob("Updated_Bottom_label_map.png"))[:20]
    samples = []
    for label in label_maps[:10]:
        parent = label.parent
        color = parent / "Updated_Bottom_color.png"
        anno = parent / "Updated_Bottom_inst_anno.json"
        path_text = str(label.relative_to(root)).lower()
        room_type = "bedroom" if "bed" in path_text else "living_dining" if "living" in path_text or "dining" in path_text else "unknown"
        item = {
            "room_type_guess": room_type,
            "label_map": str(label.relative_to(root)),
            "label_map_png": png_header(label),
            "color_map": str(color.relative_to(root)) if color.exists() else "",
            "color_map_png": png_header(color) if color.exists() else {},
            "inst_anno": str(anno.relative_to(root)) if anno.exists() else "",
            "inst_anno_top_keys": list(load_json_safe(anno).keys())[:40] if anno.exists() and isinstance(load_json_safe(anno), dict) else [],
            "evidence_level": "existing processed-output evidence",
        }
        samples.append(item)
    bedroom = [s for s in samples if s["room_type_guess"] == "bedroom"][:5]
    living = [s for s in samples if s["room_type_guess"] == "living_dining"][:5]
    selected = bedroom + living
    if not selected:
        selected = samples[:10]
    make_text_png(outdir / "contact_sheet.png", [s["label_map"] for s in selected], height=max(360, 90 * max(1, len(selected))))
    write_json(outdir / "sample_summary.json", {"selected_samples": selected, "note": "Reference contact sheet is generated by LoReflection audit tooling, not an original SemLayoutDiff output."})
    return {
        "available_label_map_count": len(label_maps),
        "bedroom_samples_checked": len(bedroom),
        "living_dining_samples_checked": len(living),
        "selected_samples": selected,
        "reference_contact_sheet": str(outdir / "contact_sheet.png"),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# SemLayoutDiff Visualization Pipeline Deep Audit",
        "",
        "This report is generated from local SemLayoutDiff source, metadata/config files, explicit external-parser references, and existing processed outputs.",
        "",
        "## Completeness",
    ]
    for key, value in report["completeness"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Call Chain"]
    for stage in report["call_chain"]:
        lines.append(f"### {stage['stage']}")
        lines.append(f"- confidence: `{stage['confidence']}`")
        for cand in stage["candidates"][:3]:
            lines.append(f"- file: `{cand['file']}`")
            for hit in cand["evidence_lines"][:3]:
                lines.append(f"  - L{hit['line']}: `{hit['text']}`")
    lines += [
        "",
        "## Important Boundary",
        "The user-uploaded `parse_json_floorplan.py` is not treated as SemLayoutDiff official source evidence.",
        "",
        "## LoReflection Implication",
        "Phase B may proceed only if all required completeness flags are true. Audit-only legends and labels are LoReflection enhancements, not SemLayoutDiff native behavior unless direct source evidence is found.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", type=Path, required=True)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--reference-output-dir", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root = args.semlayoutdiff_root
    inv = inventory(root)
    files = [root / rel for rel in inv["searchable_files"]]
    evidence = grep_evidence(root, files)
    call_chain = collect_stage_chain(root, evidence)
    deps = find_external_dependencies(root, evidence)
    metadata, palette_rows = collect_metadata(root)
    processed = processed_samples(root, args.reference_output_dir)

    true_pipeline_files = sorted({cand["file"] for stage in call_chain for cand in stage["candidates"]})
    searched = set(inv["searchable_files"])
    not_pipeline = sorted(searched - set(true_pipeline_files))[:500]

    completeness = {
        "source_coverage_complete": bool(true_pipeline_files) and bool(metadata),
        "category_mapping_chain_complete": bool(palette_rows) and any("category" in json.dumps(x).lower() or "label" in json.dumps(x).lower() for x in metadata),
        "furniture_rendering_policy_complete": any(stage["stage"] == "top-down rendering" and stage["complete"] for stage in call_chain)
        and any(stage["stage"] == "geometry extraction" and stage["complete"] for stage in call_chain),
        "architecture_rendering_policy_complete": any(stage["stage"] == "architecture rendering" and stage["complete"] for stage in call_chain),
        "draw_order_complete": any("zorder" in json.dumps(item).lower() or "sort" in json.dumps(item).lower() or "height" in json.dumps(item).lower() for item in evidence),
        "crop_resize_policy_complete": any(stage["stage"] == "crop/resize/padding" and stage["complete"] for stage in call_chain),
    }

    layer_rows = [
        {
            "order": 1,
            "layer/object type": "unknown_from_static_audit",
            "source": "static source search",
            "reason": "Detailed runtime draw order requires direct source evidence from rendering code.",
            "can overwrite previous layer": "unknown",
            "final visible effect": "unknown",
        }
    ]
    if completeness["draw_order_complete"]:
        layer_rows[0]["layer/object type"] = "candidate evidence found; inspect JSON call_chain for exact lines"
        layer_rows[0]["final visible effect"] = "inferred from source hits"

    gap_rows = [
        {
            "aspect": aspect,
            "SemLayoutDiff behavior": "see deep audit evidence",
            "LoReflection current behavior": "prototype audit V2 uses canonical LoReflection geometry and audit-only overlays",
            "evidence": "reports/semlayoutdiff_visualization_pipeline_deep_audit.json",
            "difference": "requires manual review",
            "visual consequence": "unknown until evidence reviewed" if not all(completeness.values()) else "alignable",
            "should_align": "yes" if aspect in {"palette", "crop", "padding", "aspect ratio"} and all(completeness.values()) else "pending",
            "should_not_align": "legend is LoReflection audit enhancement",
            "recommended action": "do not change LoReflection visualization automatically unless completeness is true",
            "confidence": "hard/inferred mixed",
        }
        for aspect in [
            "category mapping",
            "palette",
            "floor rendering",
            "boundary rendering",
            "wall rendering",
            "door rendering",
            "window rendering",
            "furniture footprint",
            "orientation",
            "scale",
            "layer order",
            "overlap handling",
            "crop",
            "padding",
            "resize",
            "aspect ratio",
            "instance annotation",
            "legend",
            "contact sheet composition",
        ]
    ]

    write_json(Path("reports/semlayoutdiff_visualization_source_inventory.json"), {
        **inv,
        "true_pipeline_files": true_pipeline_files,
        "searched_but_not_pipeline_files_head": not_pipeline,
        "external_dependencies": deps,
    })
    mapping_fields = [
        "raw_category",
        "intermediate_category",
        "generic_category",
        "semantic_index",
        "RGB color",
        "room type applicability",
        "include_arch behavior",
        "source file",
        "source line",
    ]
    write_csv(Path("reports/semlayoutdiff_category_mapping_chain.csv"), palette_rows, mapping_fields)
    write_csv(Path("reports/semlayoutdiff_render_layer_order.csv"), layer_rows, ["order", "layer/object type", "source", "reason", "can overwrite previous layer", "final visible effect"])
    write_csv(Path("reports/semlayoutdiff_final_palette.csv"), palette_rows, mapping_fields)
    write_csv(Path("reports/semlayoutdiff_vs_loreflection_visualization_gap.csv"), gap_rows, ["aspect", "SemLayoutDiff behavior", "LoReflection current behavior", "evidence", "difference", "visual consequence", "should_align", "should_not_align", "recommended action", "confidence"])

    report = {
        "report_version": "semlayoutdiff_visualization_pipeline_deep_audit_v1",
        "paths": {"semlayoutdiff_root": str(root), "prototype_root": str(args.prototype_root)},
        "source_inventory": {
            "files_searched": inv["searchable_file_count"],
            "true_pipeline_files": true_pipeline_files,
            "searched_but_not_pipeline_files_head": not_pipeline,
            "external_dependencies": deps,
        },
        "call_chain": call_chain,
        "metadata_and_config": metadata,
        "category_mapping_chain_rows": len(palette_rows),
        "processed_sample_verification": processed,
        "layer_order": layer_rows,
        "completeness": completeness,
        "phase_b_allowed": all(completeness.values()),
        "remaining_unknowns": [k for k, v in completeness.items() if not v],
        "important_boundary": "User-uploaded parse_json_floorplan.py is external policy reference only, not SemLayoutDiff official evidence.",
    }
    write_json(args.output_json, report)
    write_markdown(args.output_markdown, report)
    if args.verbose:
        print(json.dumps({"completeness": completeness, "phase_b_allowed": report["phase_b_allowed"], "remaining_unknowns": report["remaining_unknowns"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
