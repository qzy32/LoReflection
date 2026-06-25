#!/usr/bin/env python3
"""Inspect real 3D-FRONT / 3D-FUTURE / SemLayoutDiff / EditRoom field mappings.

This script samples a bounded number of real files and writes a mapping report.
It does not convert datasets, download files, load model weights, or train models.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from loreflection.config.paths import load_authoritative_3dfront_paths


KEYS_OF_INTEREST = ["uid", "jid", "type", "roomType", "bbox", "children", "pos", "rot", "scale", "position", "rotation"]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def safe_load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore")), None
    except Exception as exc:  # noqa: BLE001 - this is an inspection script.
        return None, repr(exc)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_value(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {"type": "dict", "keys": list(value.keys())[:60]}
    if isinstance(value, list):
        summary = {"type": "list", "length": len(value)}
        if value and isinstance(value[0], dict):
            summary["first_item_keys"] = list(value[0].keys())[:60]
        else:
            summary["first_item_type"] = type(value[0]).__name__ if value else None
        return summary
    return {"type": type(value).__name__, "repr_head": repr(value)[:120]}


def walk_limited(obj: Any, path: str = "$", depth: int = 0, max_depth: int = 5):
    if depth > max_depth:
        return
    yield path, obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from walk_limited(value, f"{path}.{key}", depth + 1, max_depth)
    elif isinstance(obj, list):
        for index, value in enumerate(obj[:20]):
            yield from walk_limited(value, f"{path}[{index}]", depth + 1, max_depth)


def find_list_candidates(data: Any, tokens: list[str], max_items: int = 12) -> list[dict[str, Any]]:
    found = []
    for path, value in walk_limited(data, max_depth=5):
        if not isinstance(value, list) or not value:
            continue
        dict_items = [x for x in value[:10] if isinstance(x, dict)]
        if not dict_items:
            continue
        keys = set()
        for item in dict_items:
            keys.update(str(k) for k in item.keys())
        joined = " ".join(k.lower() for k in keys)
        if any(token.lower() in joined or token.lower() in path.lower() for token in tokens):
            found.append({"path": path, "length": len(value), "sample_keys": sorted(keys)[:60]})
        if len(found) >= max_items:
            break
    return found


def collect_nested_keys(data: Any) -> list[str]:
    keys = set()
    for _, value in walk_limited(data, max_depth=5):
        if isinstance(value, dict):
            keys.update(str(k) for k in value.keys())
    return sorted(keys)


def collect_values_for_key(data: Any, key_name: str, limit: int = 100) -> list[Any]:
    values = []
    for _, value in walk_limited(data, max_depth=6):
        if isinstance(value, dict) and key_name in value:
            values.append(value.get(key_name))
        if len(values) >= limit:
            break
    return values


def inspect_front(root: Path, max_scenes: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "sample_count": 0,
        "json_count_estimate": 0,
        "top_level_keys": [],
        "room_field_candidates": [],
        "furniture_field_candidates": [],
        "mesh_field_candidates": [],
        "transform_field_candidates": [],
        "sample_scenes": [],
        "sample_front_jids": [],
        "can_extract": {},
        "warnings": [],
    }
    if not root.exists():
        result["warnings"].append("THREED_FRONT_SCENE_ROOT does not exist")
        return result

    samples: list[Path] = []
    for path in root.rglob("*.json"):
        result["json_count_estimate"] += 1
        name = path.name.lower()
        if name in {"texture_info.json", "model_info.json"}:
            continue
        if len(samples) < max_scenes:
            samples.append(path)

    nested_key_union = set()
    sample_jids: list[str] = []
    can_scene = can_room_type = can_furniture_jid = False
    for path in samples:
        data, error = safe_load_json(path)
        item: dict[str, Any] = {"path": str(path), "relative": str(path.relative_to(root))}
        if error:
            item["error"] = error
            result["sample_scenes"].append(item)
            continue
        if isinstance(data, dict):
            top_keys = list(data.keys())
            item["top_level_keys"] = top_keys[:80]
            result["top_level_keys"].extend(top_keys)
            item["scene_summary"] = summarize_value(data.get("scene")) if "scene" in data else None
            item["furniture_summary"] = summarize_value(data.get("furniture")) if "furniture" in data else None
            item["mesh_summary"] = summarize_value(data.get("mesh")) if "mesh" in data else None
            item["room_list_candidates"] = find_list_candidates(data, ["room", "roomType", "children", "bbox"])
            item["furniture_list_candidates"] = find_list_candidates(data, ["furniture", "jid", "uid", "model", "transform"])
            item["key_presence"] = {key: bool(collect_values_for_key(data, key, 1)) for key in KEYS_OF_INTEREST}
            nested = collect_nested_keys(data)
            nested_key_union.update(nested)
            jids = [x for x in collect_values_for_key(data, "jid", 200) if isinstance(x, str)]
            sample_jids.extend(jids)
            can_scene = can_scene or bool(data.get("uid"))
            can_room_type = can_room_type or bool(collect_values_for_key(data, "roomType", 1) or collect_values_for_key(data, "type", 1))
            can_furniture_jid = can_furniture_jid or bool(jids)
            item["sample_jids"] = jids[:20]
        else:
            item["top_type"] = type(data).__name__
        result["sample_scenes"].append(item)

    nested_keys = sorted(nested_key_union)
    result["sample_count"] = len(samples)
    result["top_level_keys"] = sorted(set(result["top_level_keys"]))
    result["room_field_candidates"] = [k for k in nested_keys if any(t in k.lower() for t in ["room", "scene", "children", "bbox", "type"])]
    result["furniture_field_candidates"] = [k for k in nested_keys if any(t in k.lower() for t in ["furniture", "jid", "uid", "model"])]
    result["mesh_field_candidates"] = [k for k in nested_keys if any(t in k.lower() for t in ["mesh", "boundary", "wall", "floor", "ceiling"])]
    result["transform_field_candidates"] = [k for k in nested_keys if any(t in k.lower() for t in ["pos", "rot", "scale", "transform", "translate"])]
    result["sample_front_jids"] = sorted(set(sample_jids))[:100]
    result["can_extract"] = {
        "scene_id": can_scene,
        "room_id": bool(collect_values_for_key(result["sample_scenes"], "roomId", 1)),
        "room_type": can_room_type,
        "furniture_jid": can_furniture_jid,
        "furniture_transform": any(k in nested_keys for k in ["pos", "rot", "scale", "position", "rotation"]),
        "mesh_or_boundary_candidate": bool(result["mesh_field_candidates"]),
    }
    return result


def inspect_future(root: Path, model_info: Path, front_jids: list[str], max_models: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "model_info_exists": model_info.exists(),
        "model_count": 0,
        "id_field_candidates": [],
        "category_field_candidates": [],
        "style_theme_material_fields": [],
        "size_bbox_fields": [],
        "sample_models": [],
        "jid_match_check": {"sample_front_jids": front_jids[:30], "matched": [], "unmatched": []},
        "can_build_jid_to_category": False,
        "can_build_jid_to_metadata": False,
        "warnings": [],
    }
    if not model_info.exists():
        result["warnings"].append("model_info.json does not exist")
        return result
    data, error = safe_load_json(model_info)
    if error:
        result["warnings"].append(error)
        return result
    if not isinstance(data, list):
        result["warnings"].append(f"model_info top type is {type(data).__name__}, expected list")
        return result
    result["model_count"] = len(data)
    sample = [x for x in data[:max_models] if isinstance(x, dict)]
    result["sample_models"] = sample
    all_keys = sorted({str(k) for item in sample for k in item.keys()})
    result["id_field_candidates"] = [k for k in all_keys if any(t in k.lower() for t in ["id", "uid", "jid", "model"])]
    result["category_field_candidates"] = [k for k in all_keys if any(t in k.lower() for t in ["category", "class", "name", "title"])]
    result["style_theme_material_fields"] = [k for k in all_keys if any(t in k.lower() for t in ["style", "theme", "material"])]
    result["size_bbox_fields"] = [k for k in all_keys if any(t in k.lower() for t in ["size", "bbox", "dim", "scale"])]

    index = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        for key in ["model_id", "jid", "uid", "id"]:
            value = item.get(key)
            if isinstance(value, str):
                index[value] = item
    matched = []
    unmatched = []
    for jid in front_jids[:30]:
        if jid in index:
            matched.append({"jid": jid, "category": index[jid].get("category") or index[jid].get("super-category")})
        else:
            unmatched.append(jid)
    result["jid_match_check"] = {"sample_front_jids": front_jids[:30], "matched": matched, "unmatched": unmatched}
    result["can_build_jid_to_category"] = bool(index and result["category_field_candidates"])
    result["can_build_jid_to_metadata"] = bool(index)
    return result


def png_info(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path)}
    try:
        with path.open("rb") as f:
            head = f.read(32)
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height = struct.unpack(">II", head[16:24])
            color_type = head[25] if len(head) > 25 else None
            info.update({"format": "PNG", "width": width, "height": height, "mode_hint": color_type})
    except Exception as exc:  # noqa: BLE001
        info["error"] = repr(exc)
    return info


def inspect_semlayoutdiff(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "semantic_png_candidates": [],
        "json_candidates": [],
        "npy_candidates": [],
        "pkl_candidates": [],
        "alignment_with_front": "unknown",
        "can_source_architecture_condition": "uncertain",
        "can_source_semantic_layout": "uncertain",
        "warnings": [],
    }
    if not root.exists():
        result["warnings"].append("SEMLAYOUTDIFF_ROOT does not exist")
        return result
    pngs = []
    jsons = []
    npys = []
    pkls = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        suffix = path.suffix.lower()
        if suffix == ".png" and ("label" in name.lower() or "semantic" in name.lower() or "bottom" in name.lower()):
            pngs.append(path)
        elif suffix == ".json" and ("meta" in name.lower() or "anno" in name.lower() or len(jsons) < 20):
            jsons.append(path)
        elif suffix in {".npy", ".npz"}:
            npys.append(path)
        elif suffix == ".pkl":
            pkls.append(path)
        if len(pngs) >= 40 and len(jsons) >= 40 and len(npys) >= 20 and len(pkls) >= 20:
            break
    result["semantic_png_candidates"] = [png_info(p) for p in pngs[:20]]
    for p in jsons[:20]:
        data, error = safe_load_json(p)
        item = {"path": str(p)}
        if error:
            item["error"] = error
        elif isinstance(data, dict):
            item["top_level_keys"] = list(data.keys())[:60]
        elif isinstance(data, list):
            item["top_type"] = "list"
            item["length"] = len(data)
            if data and isinstance(data[0], dict):
                item["first_item_keys"] = list(data[0].keys())[:60]
        result["json_candidates"].append(item)
    result["npy_candidates"] = [str(p) for p in npys[:20]]
    result["pkl_candidates"] = [str(p) for p in pkls[:20]]
    result["can_source_semantic_layout"] = "yes" if result["semantic_png_candidates"] else "uncertain"
    result["can_source_architecture_condition"] = "uncertain"
    return result


def inspect_editroom(root: Path) -> dict[str, Any]:
    key_files = [
        "tools/generate_perturbations.py",
        "tools/editroomperturb.py",
        "tools/generate_prompt.py",
        "src/train_edit.py",
        "configs/bedroom_sg2sc_diffusion.yaml",
        "configs/bedroom_sg_diffusion.yaml",
    ]
    result: dict[str, Any] = {
        "root": str(root),
        "repo_exists": root.exists(),
        "key_files": {},
        "dataset_dirs": [],
        "manifest_candidates": [],
        "current_blocking": [],
    }
    if not root.exists():
        result["current_blocking"].append("EDITROOM_ROOT does not exist")
        return result
    for rel in key_files:
        result["key_files"][rel] = (root / rel).exists()
    ds = root / "datasets"
    if ds.exists():
        result["dataset_dirs"] = [str(p) for p in sorted(ds.rglob("*")) if p.is_dir()][:80]
    for p in root.rglob("*"):
        try:
            is_file = p.is_file()
        except OSError as exc:
            result.setdefault("warnings", []).append(f"skip unreadable path: {p}: {exc}")
            continue
        if is_file and p.suffix.lower() in {".json", ".yaml", ".yml"} and any(t in p.name.lower() for t in ["prompt", "perturb", "edit", "manifest"]):
            result["manifest_candidates"].append(str(p))
            if len(result["manifest_candidates"]) >= 40:
                break
    missing_tools = [k for k, ok in result["key_files"].items() if k.startswith("tools/") and not ok]
    if missing_tools:
        result["current_blocking"].append("Missing EditRoom tools affect future editing baseline / perturbation generation, but not current 3D field mapping.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-scenes", type=int, default=5)
    parser.add_argument("--max-models", type=int, default=20)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    env = read_env(args.env_file)
    dataset_paths = load_authoritative_3dfront_paths(args.env_file)
    paths = {
        "THREED_FRONT_SCENE_ROOT": dataset_paths.scene_root.as_posix(),
        "THREED_FUTURE_MODEL_ROOT": dataset_paths.future_model_root.as_posix(),
        "THREED_FUTURE_MODEL_INFO": dataset_paths.future_model_info.as_posix(),
        "SEMLAYOUTDIFF_ROOT": env.get("SEMLAYOUTDIFF_ROOT", ""),
        "EDITROOM_ROOT": env.get("EDITROOM_ROOT", ""),
    }
    front = inspect_front(dataset_paths.scene_root, args.max_scenes)
    future = inspect_future(dataset_paths.future_model_root, dataset_paths.future_model_info, front.get("sample_front_jids", []), args.max_models)
    sld = inspect_semlayoutdiff(Path(paths["SEMLAYOUTDIFF_ROOT"]))
    editroom = inspect_editroom(Path(paths["EDITROOM_ROOT"]))

    blocking = []
    if not front.get("exists"):
        blocking.append("THREED_FRONT_SCENE_ROOT missing")
    if not future.get("model_info_exists"):
        blocking.append("THREED_FUTURE_MODEL_INFO missing")
    if not front.get("can_extract", {}).get("furniture_jid"):
        blocking.append("No furniture jid sampled from 3D-FRONT")
    if not future.get("can_build_jid_to_category"):
        blocking.append("3D-FUTURE model_id/jid to category mapping uncertain")

    recommended = {
        "architecture_json": {
            "scene_id": "3D-FRONT top-level uid",
            "room_candidates": front.get("room_field_candidates", []),
            "mesh_boundary_candidates": front.get("mesh_field_candidates", []),
            "transform_candidates": front.get("transform_field_candidates", []),
        },
        "furniture_category_mapping": {
            "front_field": "furniture[].jid or nested jid",
            "future_id_field_candidates": future.get("id_field_candidates", []),
            "future_category_field_candidates": future.get("category_field_candidates", []),
            "feasible": "yes" if future.get("can_build_jid_to_category") and future.get("jid_match_check", {}).get("matched") else "uncertain",
        },
        "semantic_layout_mapping": {
            "source": "SemLayoutDiff Updated_Bottom_label_map.png candidates" if sld.get("semantic_png_candidates") else "unknown",
            "feasible": "yes" if sld.get("semantic_png_candidates") else "uncertain",
        },
        "val50_feasibility": "partial" if blocking else "yes",
        "blocking_issues": blocking,
    }
    report = {
        "report_version": "real_field_mapping_v1",
        "schema_version": "real-field-mapping-report-v1",
        "paths": paths,
        "threed_front": front,
        "threed_future": future,
        "semlayoutdiff": sld,
        "editroom": editroom,
        "recommended_mapping": recommended,
    }
    write_json(args.output, report)
    if args.verbose:
        print(json.dumps({
            "output": str(args.output),
            "front_samples": front.get("sample_count"),
            "future_models": future.get("model_count"),
            "matched_jids": future.get("jid_match_check", {}).get("matched", [])[:10],
            "blocking_issues": blocking,
            "val50_feasibility": recommended["val50_feasibility"],
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
