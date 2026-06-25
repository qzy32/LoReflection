#!/usr/bin/env python
"""Mine reference 3D-FRONT preprocessing pipelines.

This read-only tool inspects existing SemLayoutDiff and EditRoom repositories,
plus the bounded 5-scene LoReflection prototype, to find reference evidence for
category mapping, object transforms, room boundaries, semantic maps, and boxes.
It does not run the referenced pipelines, load model weights, train models, or
convert the full dataset.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TEXT_SUFFIXES = {".py", ".json", ".yaml", ".yml", ".txt", ".md", ".csv", ".sh", ".cfg"}
MAX_TEXT_BYTES = 900_000
MAX_FILES_PER_ROOT = 5000
MAX_EVIDENCE_LINES = 20

SEMLAYOUTDIFF_FILENAME_HINTS = (
    "data_processor.py",
    "data_to_npy.py",
    "sample_layout.py",
    "dataset",
    "preprocess",
    "palette",
    "label",
    "class",
    "category",
    "semantic",
    "room_mask",
    "boxes",
    "npy",
)

SEMLAYOUTDIFF_KEYWORDS = (
    "palette",
    "label",
    "class",
    "category",
    "semantic",
    "room_mask",
    "boxes.npz",
    "boxes",
    "Updated_Bottom_label_map.png",
    "jid",
    "uid",
    "pos",
    "rot",
    "scale",
    "bbox",
    "mesh",
)

EDITROOM_KEYWORDS = (
    "3D-FRONT",
    "3D-FUTURE",
    "model_info",
    "threed_front.pkl",
    "pickle",
    "dataset",
    "preprocess",
    "category",
    "bbox",
    "center",
    "size",
    "angle",
    "rotation",
    "translation",
    "room",
    "scene",
    "InstructScene",
    "perturb",
    "prompt",
)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def iter_files(root: Path, max_files: int = MAX_FILES_PER_ROOT, skip_extra: set[str] | None = None) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    skip_dirs = {".git", "__pycache__", ".venv", "venv", "outputs", "logs", "tmp", "models"}
    if skip_extra:
        skip_dirs.update(skip_extra)
    for current, dirs, names in os.walk(root):
        dirs.sort()
        names.sort()
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in names:
            files.append(Path(current) / name)
            if len(files) >= max_files:
                return files
    return files


def is_text_candidate(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= MAX_TEXT_BYTES
    except OSError:
        return False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def grep_lines(path: Path, keywords: tuple[str, ...], max_lines: int = MAX_EVIDENCE_LINES) -> list[dict[str, Any]]:
    if not is_text_candidate(path):
        return []
    text = read_text(path)
    hits: list[dict[str, Any]] = []
    lowered_keywords = [(kw, kw.lower()) for kw in keywords]
    for lineno, line in enumerate(text.splitlines(), 1):
        line_lower = line.lower()
        found = [kw for kw, kw_lower in lowered_keywords if kw_lower in line_lower]
        if not found:
            continue
        stripped = re.sub(r"\s+", " ", line.strip())
        if not stripped:
            continue
        hits.append({"line": lineno, "keywords": found[:6], "text": stripped[:220]})
        if len(hits) >= max_lines:
            break
    return hits


def extract_functions(path: Path) -> list[dict[str, Any]]:
    if not is_text_candidate(path) or path.suffix.lower() != ".py":
        return []
    out = []
    for lineno, line in enumerate(read_text(path).splitlines(), 1):
        match = re.match(r"\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
        if match:
            out.append({"name": match.group(1), "line": lineno})
    return out[:80]


def keyword_set(path: Path, keywords: tuple[str, ...]) -> list[str]:
    if not is_text_candidate(path):
        return []
    text = read_text(path).lower()
    return [kw for kw in keywords if kw.lower() in text]


def file_record(path: Path, root: Path, keywords: tuple[str, ...]) -> dict[str, Any]:
    return {
        "file": rel(path, root),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "functions": extract_functions(path),
        "keywords_found": keyword_set(path, keywords),
        "evidence_lines": grep_lines(path, keywords),
    }


def find_named_files(root: Path, names: tuple[str, ...]) -> list[str]:
    records = []
    for path in iter_files(root, max_files=20000, skip_extra={"datasets", "data"}):
        lower = path.name.lower()
        if any(name.lower() == lower for name in names):
            records.append(rel(path, root))
    return sorted(records)[:100]


def mine_semlayoutdiff(root: Path) -> dict[str, Any]:
    files = iter_files(root, max_files=20000, skip_extra={"datasets", "data", "plan_json_0327"})
    artifact_files = iter_files(root, max_files=12000)
    category_files: list[dict[str, Any]] = []
    palette_files: list[dict[str, Any]] = []
    class_vocab_candidates: list[dict[str, Any]] = []
    category_mapping_candidates: list[dict[str, Any]] = []
    label_color_mapping_candidates: list[dict[str, Any]] = []
    geometry_parser_candidates: list[dict[str, Any]] = []
    semantic_artifact_candidates: list[str] = []

    for path in artifact_files:
        rel_name = rel(path, root)
        lower = rel_name.lower()
        if path.name == "Updated_Bottom_label_map.png" or any(token in lower for token in ("semantic", "room_mask", "boxes")) and path.suffix.lower() in {".png", ".npy", ".npz", ".pkl", ".json"}:
            semantic_artifact_candidates.append(rel_name)

    for path in files:
        rel_name = rel(path, root)
        lower = rel_name.lower()
        if not is_text_candidate(path):
            continue
        kws = keyword_set(path, SEMLAYOUTDIFF_KEYWORDS)
        if not kws:
            continue
        record = file_record(path, root, SEMLAYOUTDIFF_KEYWORDS)
        if any(token in lower for token in ("category", "class", "label", "dataset", "data_processor")):
            category_files.append(record)
        if any(token in lower for token in ("palette", "color", "label")) or "palette" in kws:
            palette_files.append(record)
        if any(token in " ".join(line["text"].lower() for line in record["evidence_lines"]) for token in ("classes", "class_labels", "object_types", "labels")):
            class_vocab_candidates.append(record)
        if "category" in kws or "class" in kws or "label" in kws:
            category_mapping_candidates.append(record)
        if "palette" in kws or "label" in kws:
            label_color_mapping_candidates.append(record)
        if any(kw in kws for kw in ("jid", "uid", "pos", "rot", "scale", "bbox", "mesh", "room_mask", "boxes")):
            geometry_parser_candidates.append(record)

    return {
        "exists": root.exists(),
        "key_files": find_named_files(root, ("data_processor.py", "data_to_npy.py", "sample_layout.py")),
        "category_files": category_files[:20],
        "palette_files": palette_files[:20],
        "class_vocab_candidates": class_vocab_candidates[:20],
        "category_mapping_candidates": category_mapping_candidates[:20],
        "label_color_mapping_candidates": label_color_mapping_candidates[:20],
        "geometry_parser_candidates": geometry_parser_candidates[:30],
        "semantic_artifact_candidates": sorted(semantic_artifact_candidates)[:100],
    }


def mine_editroom(root: Path) -> dict[str, Any]:
    files = iter_files(root, max_files=20000, skip_extra={"datasets", "data"})
    data_files = iter_files(root / "datasets", max_files=8000) if (root / "datasets").exists() else []
    dataset_preprocess_files: list[dict[str, Any]] = []
    category_transform_candidates: list[dict[str, Any]] = []
    edit_pair_evidence: list[dict[str, Any]] = []
    pkl_files: list[dict[str, Any]] = []
    threed_front_pkl_usage: list[dict[str, Any]] = []

    for path in data_files:
        rel_name = rel(path, root)
        if path.suffix.lower() == ".pkl":
            pkl_files.append({"file": rel_name, "size_bytes": path.stat().st_size})

    for path in files:
        rel_name = rel(path, root)
        lower = rel_name.lower()
        if path.suffix.lower() == ".pkl":
            pkl_files.append({"file": rel_name, "size_bytes": path.stat().st_size})
        if not is_text_candidate(path):
            continue
        kws = keyword_set(path, EDITROOM_KEYWORDS)
        if not kws:
            continue
        record = file_record(path, root, EDITROOM_KEYWORDS)
        if any(token in lower for token in ("dataset", "preprocess", "3d-front", "3d_future", "threed")):
            dataset_preprocess_files.append(record)
        if any(kw in kws for kw in ("category", "bbox", "center", "size", "angle", "rotation", "translation", "scene", "room")):
            category_transform_candidates.append(record)
        if any(kw in kws for kw in ("perturb", "prompt", "InstructScene")):
            edit_pair_evidence.append(record)
        if "threed_front.pkl" in read_text(path).lower():
            threed_front_pkl_usage.append(record)

    return {
        "exists": root.exists(),
        "dataset_preprocess_files": dataset_preprocess_files[:25],
        "pkl_files": sorted(pkl_files, key=lambda x: x["file"])[:100],
        "threed_front_pkl_usage": threed_front_pkl_usage[:20],
        "category_transform_parser_candidates": category_transform_candidates[:25],
        "edit_pair_data_evidence": edit_pair_evidence[:25],
        "key_files": {
            "tools/generate_perturbations.py": (root / "tools/generate_perturbations.py").exists(),
            "tools/editroomperturb.py": (root / "tools/editroomperturb.py").exists(),
            "tools/generate_prompt.py": (root / "tools/generate_prompt.py").exists(),
            "src/train_edit.py": (root / "src/train_edit.py").exists(),
            "configs/bedroom_sg2sc_diffusion.yaml": (root / "configs/bedroom_sg2sc_diffusion.yaml").exists(),
            "configs/bedroom_sg_diffusion.yaml": (root / "configs/bedroom_sg_diffusion.yaml").exists(),
        },
    }


def find_scene_children(scene: Any) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []

    def scan(node: Any, path: str = "", depth: int = 0) -> None:
        if depth > 7:
            return
        if isinstance(node, dict):
            has_ref = any(k in node for k in ("ref", "instanceid", "instanceId", "uid", "jid"))
            has_transform = any(k in node for k in ("pos", "position", "rot", "rotation", "scale", "bbox", "transform"))
            if has_ref and has_transform:
                item = dict(node)
                item["_path"] = path
                children.append(item)
            for key, value in node.items():
                scan(value, f"{path}.{key}" if path else str(key), depth + 1)
        elif isinstance(node, list):
            for idx, value in enumerate(node[:200]):
                scan(value, f"{path}[{idx}]", depth + 1)

    scan(scene)
    return children


def diagnose_selected_scenes(prototype_root: Path) -> dict[str, Any]:
    source_root = prototype_root / "source_samples" / "scene_json"
    scene_files = sorted(source_root.glob("*.json"))
    link_counts = Counter()
    room_path_counts = Counter()
    mesh_key_counts = Counter()
    furniture_counts = []
    transform_examples = []
    boundary_candidates = Counter()
    category_examples = []

    for path in scene_files:
        try:
            scene = load_json(path)
        except Exception:
            continue
        furniture = scene.get("furniture", []) if isinstance(scene, dict) else []
        furniture = [x for x in furniture if isinstance(x, dict)]
        furniture_counts.append(len(furniture))
        uid_set = {str(x.get("uid")) for x in furniture if x.get("uid") is not None}
        jid_set = {str(x.get("jid")) for x in furniture if x.get("jid") is not None}
        children = find_scene_children(scene)
        for child in children:
            ref_values = {
                "ref": str(child.get("ref")) if child.get("ref") is not None else "",
                "instanceid": str(child.get("instanceid") or child.get("instanceId") or ""),
                "uid": str(child.get("uid")) if child.get("uid") is not None else "",
                "jid": str(child.get("jid")) if child.get("jid") is not None else "",
            }
            for key, value in ref_values.items():
                if value and value in uid_set:
                    link_counts[f"child.{key} -> furniture.uid"] += 1
                if value and value in jid_set:
                    link_counts[f"child.{key} -> furniture.jid"] += 1
            if len(transform_examples) < 10:
                transform_examples.append(
                    {
                        "scene": path.name,
                        "path": child.get("_path"),
                        "keys": sorted(k for k in child.keys() if not k.startswith("_"))[:30],
                        "ref": child.get("ref"),
                        "instanceid": child.get("instanceid") or child.get("instanceId"),
                        "pos": child.get("pos") or child.get("position"),
                        "rot": child.get("rot") or child.get("rotation"),
                        "scale": child.get("scale"),
                    }
                )
        scene_obj = scene.get("scene") if isinstance(scene, dict) else None
        if isinstance(scene_obj, dict):
            rooms = scene_obj.get("room") or scene_obj.get("rooms")
            if isinstance(rooms, list):
                for idx, room in enumerate(rooms[:20]):
                    if isinstance(room, dict):
                        room_path_counts[f"scene.room[{idx}]"] += 1
                        if "children" in room:
                            boundary_candidates["scene.room.children"] += 1
                        if "bbox" in room:
                            boundary_candidates["scene.room.bbox"] += 1
        mesh = scene.get("mesh") if isinstance(scene, dict) else None
        if isinstance(mesh, list):
            boundary_candidates["top_level.mesh"] += 1
            for item in mesh[:20]:
                if isinstance(item, dict):
                    for key in item.keys():
                        mesh_key_counts[key] += 1
        for item in furniture[:10]:
            category_examples.append({"uid": item.get("uid"), "jid": item.get("jid"), "category": item.get("category"), "type": item.get("type")})

    best_link_rule = link_counts.most_common(1)[0][0] if link_counts else "unknown"
    transform_location = "scene.room.children" if any("scene.room" in ex.get("path", "") for ex in transform_examples) else "nested scene child nodes / unknown"
    boundary_source = "top_level.mesh or scene.room.bbox candidate" if boundary_candidates else "unknown"
    return {
        "scene_count": len(scene_files),
        "furniture_counts": furniture_counts,
        "link_rule_counts": dict(link_counts.most_common()),
        "likely_transform_location": transform_location,
        "best_furniture_to_scene_node_link_rule": best_link_rule,
        "transform_examples": transform_examples,
        "room_path_counts": dict(room_path_counts),
        "mesh_key_counts": dict(mesh_key_counts.most_common(50)),
        "boundary_source_candidate": boundary_source,
        "boundary_candidates": dict(boundary_candidates),
        "category_examples": category_examples[:20],
        "category_mapping_source_candidate": "SemLayoutDiff category vocabulary plus 3D-FUTURE model_info, adapted to LoReflection palette",
    }


def build_repair_plan(semlayoutdiff: dict[str, Any], editroom: dict[str, Any], diagnosis: dict[str, Any]) -> dict[str, Any]:
    category_source = "SemLayoutDiff / ATISS-style vocabulary adapted with LoReflection palette"
    if not semlayoutdiff.get("category_mapping_candidates"):
        category_source = "custom from model_info, then validate against SemLayoutDiff if evidence is sparse"
    transform_source = "3D-FRONT scene child transform parser"
    if diagnosis.get("best_furniture_to_scene_node_link_rule") == "unknown":
        transform_source = "needs additional selected-scene inspection"
    return {
        "category_mapping": {
            "reference_source": category_source,
            "actions": [
                "Extract class vocabulary and category normalization rules from SemLayoutDiff/ATISS-style preprocessing evidence.",
                "Map 3D-FUTURE model_info category and super-category to LoReflection palette categories instead of leaving raw strings as unknown.",
                "Record unknown/raw category histogram before scaling beyond 5 scenes.",
            ],
        },
        "transform_extraction": {
            "reference_source": transform_source,
            "link_rules": [
                diagnosis.get("best_furniture_to_scene_node_link_rule", "unknown"),
                "fallback: inspect child.ref / child.instanceid / child.uid against furniture.uid before using grid placement",
            ],
            "actions": [
                "Parse nested scene room children and transform-bearing nodes before using category-prior grid fallback.",
                "Store explicit mapping_status for each furniture instance: transform_matched, transform_missing, or category_prior_size.",
                "Add a regression check that missing transform fallback drops below the current 30/167 baseline.",
            ],
        },
        "boundary_extraction": {
            "reference_source": "SemLayoutDiff room_mask / mesh processing evidence plus 3D-FRONT mesh fields",
            "actions": [
                "Inspect mesh entries and room nodes to recover floor polygon candidates before bbox_fallback.",
                "If room mask exists in SemLayoutDiff processed outputs, use it as validation evidence, not as raw geometry source.",
                "Keep boundary_source in Architecture JSON and fail val50 scaling if all scenes remain bbox_fallback.",
            ],
        },
        "do_not_do": [
            "Do not treat SemLayoutDiff processed PNG as the raw source.",
            "Do not scale to 50 using only bbox fallback.",
            "Do not treat unknown category as a real semantic category.",
            "Do not assume the EditRoom bundle is a freshly downloaded official archive.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semlayoutdiff-root", type=Path, required=True)
    parser.add_argument("--editroom-root", type=Path, required=True)
    parser.add_argument("--threed-front-root", type=Path, required=True)
    parser.add_argument("--threed-future-root", type=Path, required=True)
    parser.add_argument("--prototype-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    semlayoutdiff = mine_semlayoutdiff(args.semlayoutdiff_root)
    editroom = mine_editroom(args.editroom_root)
    diagnosis = diagnose_selected_scenes(args.prototype_root)
    repair_plan = build_repair_plan(semlayoutdiff, editroom, diagnosis)
    report = {
        "report_version": "reference_3dfront_pipeline_mining_v1",
        "paths": {
            "semlayoutdiff_root": args.semlayoutdiff_root.as_posix(),
            "editroom_root": args.editroom_root.as_posix(),
            "threed_front_root": args.threed_front_root.as_posix(),
            "threed_future_root": args.threed_future_root.as_posix(),
            "prototype_root": args.prototype_root.as_posix(),
        },
        "semlayoutdiff": semlayoutdiff,
        "editroom": editroom,
        "selected_scene_diagnosis": diagnosis,
        "recommended_converter_repair": repair_plan,
        "safety": {
            "downloaded_data": False,
            "downloaded_models": False,
            "training_started": False,
            "full_conversion_started": False,
            "third_party_code_executed": False,
        },
    }
    write_json(args.output, report)
    if args.verbose:
        summary = {
            "semlayoutdiff_category_candidates": len(semlayoutdiff.get("category_mapping_candidates", [])),
            "semlayoutdiff_geometry_candidates": len(semlayoutdiff.get("geometry_parser_candidates", [])),
            "editroom_parser_candidates": len(editroom.get("category_transform_parser_candidates", [])),
            "selected_scene_link_rules": diagnosis.get("link_rule_counts", {}),
            "output": args.output.as_posix(),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote reference mining report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
