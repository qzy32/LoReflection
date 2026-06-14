#!/usr/bin/env python
"""Audit LoReflection toy-level interface consistency after adapter changes."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from pathlib import Path


ABSOLUTE_PATH_PATTERNS = ["C:/", "C:\\", "/Users/", "/home/", "/mnt/"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_enum_values(node) -> set[str]:
    values: set[str] = set()
    if isinstance(node, dict):
        enum = node.get("enum")
        if isinstance(enum, list):
            values.update(item for item in enum if isinstance(item, str))
        for value in node.values():
            values.update(collect_enum_values(value))
    elif isinstance(node, list):
        for item in node:
            values.update(collect_enum_values(item))
    return values


def mask_type_schema(schema_path: Path) -> list[str]:
    values = collect_enum_values(load_json(schema_path))
    return sorted(value for value in values if value in {"bbox", "polygon", "instance_ref", "old_new_union"})


def action_type_schema(schema_path: Path) -> list[str]:
    values = collect_enum_values(load_json(schema_path))
    return sorted(value for value in values if value in {"INSERT", "DELETE", "REPLACE", "MOVE", "ADJUST_ORIENTATION"})


def runtime_mask_types(runtime_path: Path) -> list[str]:
    text = runtime_path.read_text(encoding="utf-8")
    return sorted(set(re.findall(r'item_type == "([^"]+)"', text)))


def adapter_declared_mask_types(adapter_path: Path) -> list[str]:
    text = adapter_path.read_text(encoding="utf-8")
    values = set(re.findall(r'"type": "([^"]+)"', text))
    return sorted(value for value in values if value in {"bbox", "polygon", "instance_ref", "old_new_union"})


def adapter_action_types(repairplan_builder: Path) -> list[str]:
    tree = ast.parse(repairplan_builder.read_text(encoding="utf-8"))
    actions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ACTION_MAP" and isinstance(node.value, ast.Dict):
                    for value in node.value.values:
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            actions.add(value.value)
    return sorted(actions)


def output_mask_types(root: Path) -> list[str]:
    values: set[str] = set()
    for path in root.rglob("*.json"):
        try:
            data = load_json(path)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("schema_version") == "mask-spec-v1":
            values.update(item.get("type") for item in data.get("items", []) if item.get("type"))
    return sorted(values)


def output_action_types(root: Path) -> list[str]:
    values: set[str] = set()
    for path in root.rglob("*.json"):
        try:
            data = load_json(path)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("schema_version") == "repairplan-v1":
            values.add(data.get("action_type"))
    return sorted(value for value in values if value)


def scan_absolute_paths(roots: list[Path]) -> list[dict]:
    violations = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(list(root.rglob("*.json")) + list(root.rglob("*.csv"))):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in ABSOLUTE_PATH_PATTERNS:
                if pattern in text:
                    violations.append({"file": str(path), "pattern": pattern})
    return violations


def check_diffsynth_metadata(path: Path, dataset_root: Path) -> dict:
    result = {"exists": path.exists(), "columns_ok": False, "paths_relative": True, "files_exist": True, "rows": 0, "errors": []}
    if not path.exists():
        result["errors"].append("metadata.csv missing")
        return result
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    expected = {"image", "blockwise_controlnet_image", "blockwise_controlnet_inpaint_mask", "prompt"}
    result["rows"] = len(rows)
    result["columns_ok"] = bool(rows) and set(rows[0].keys()) == expected
    if not result["columns_ok"]:
        result["errors"].append("metadata columns mismatch or no rows")
    for row in rows:
        for key in ["image", "blockwise_controlnet_image", "blockwise_controlnet_inpaint_mask"]:
            value = row.get(key, "")
            if Path(value).is_absolute() or any(pattern in value for pattern in ABSOLUTE_PATH_PATTERNS):
                result["paths_relative"] = False
                result["errors"].append(f"{key} is absolute: {value}")
            if not (dataset_root / value).exists():
                result["files_exist"] = False
                result["errors"].append(f"{key} file missing: {value}")
    return result


def check_qwenvl_export(path: Path) -> dict:
    result = {"exists": path.exists(), "format_ok": False, "paths_relative": True, "gpt_json_ok": True, "rows": 0, "errors": []}
    if not path.exists():
        result["errors"].append("Qwen-VL export missing")
        return result
    data = load_json(path)
    result["rows"] = len(data) if isinstance(data, list) else 0
    result["format_ok"] = isinstance(data, list) and all(isinstance(row, dict) and {"image", "conversations"}.issubset(row) for row in data)
    if not result["format_ok"]:
        result["errors"].append("Qwen-VL export is not image + conversations list")
        return result
    for row in data:
        image = row.get("image", "")
        if Path(image).is_absolute() or any(pattern in image for pattern in ABSOLUTE_PATH_PATTERNS):
            result["paths_relative"] = False
            result["errors"].append(f"image path is absolute: {image}")
        conv = row.get("conversations", [])
        if len(conv) < 2:
            result["format_ok"] = False
            result["errors"].append("conversations has fewer than two turns")
            continue
        if "[CORRECTION_PLANNING" not in conv[0].get("value", ""):
            result["format_ok"] = False
            result["errors"].append("human message missing correction planning token")
        try:
            json.loads(conv[1].get("value", ""))
        except json.JSONDecodeError as exc:
            result["gpt_json_ok"] = False
            result["errors"].append(f"gpt message is not strict JSON: {exc}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--editroom-output-root", type=Path, default=Path("outputs/editroom_toy_loreflection"), help="EditRoom toy output root.")
    parser.add_argument("--semlayoutdiff-output-root", type=Path, default=Path("outputs/semlayoutdiff_toy_loreflection"), help="SemLayoutDiff toy output root.")
    parser.add_argument("--toy-samples-root", type=Path, default=Path("examples/toy_samples"), help="Base toy samples root.")
    parser.add_argument("--qwenvl-export", type=Path, default=Path("outputs/editroom_toy_loreflection/planner_sft_v1/qwenvl_export_check.json"), help="Qwen-VL export JSON to audit.")
    parser.add_argument("--diffsynth-metadata", type=Path, default=Path("outputs/editroom_toy_loreflection/diffsynth_export_check/metadata.csv"), help="DiffSynth metadata.csv to audit.")
    parser.add_argument("--report", type=Path, default=Path("reports/interface_audit_v1.json"), help="Output audit report JSON.")
    args = parser.parse_args()

    schema_masks = mask_type_schema(Path("schemas/mask_spec_v1.schema.json"))
    runtime_masks = runtime_mask_types(Path("runtime/mask_tensor_adapter.py"))
    adapter_declared_masks = adapter_declared_mask_types(Path("tools/build_mask_spec_from_editroom_pair.py"))
    adapter_output_masks = output_mask_types(args.editroom_output_root)
    schema_actions = action_type_schema(Path("schemas/repairplan_v1.schema.json"))
    adapter_actions = adapter_action_types(Path("tools/build_repairplan_from_editroom_pair.py"))
    adapter_output_actions = output_action_types(args.editroom_output_root)
    mask_mismatches = []
    if set(schema_masks) - set(runtime_masks):
        mask_mismatches.append({"schema_not_runtime": sorted(set(schema_masks) - set(runtime_masks))})
    if set(runtime_masks) - set(schema_masks):
        mask_mismatches.append({"runtime_not_schema": sorted(set(runtime_masks) - set(schema_masks))})
    if set(adapter_declared_masks) - set(schema_masks):
        mask_mismatches.append({"adapter_declared_not_schema": sorted(set(adapter_declared_masks) - set(schema_masks))})
    if set(adapter_output_masks) - set(schema_masks):
        mask_mismatches.append({"adapter_outputs_not_schema": sorted(set(adapter_output_masks) - set(schema_masks))})
    action_mismatches = []
    if set(adapter_actions) - set(schema_actions):
        action_mismatches.append({"adapter_not_schema": sorted(set(adapter_actions) - set(schema_actions))})
    if set(adapter_output_actions) - set(schema_actions):
        action_mismatches.append({"adapter_outputs_not_schema": sorted(set(adapter_output_actions) - set(schema_actions))})

    absolute_violations = scan_absolute_paths([args.toy_samples_root, args.semlayoutdiff_output_root, args.editroom_output_root])
    diffsynth_check = check_diffsynth_metadata(args.diffsynth_metadata, args.diffsynth_metadata.parent)
    qwenvl_check = check_qwenvl_export(args.qwenvl_export)
    frozen = not mask_mismatches and not action_mismatches and not absolute_violations and not diffsynth_check["errors"] and not qwenvl_check["errors"]
    report = {
        "schema_version": "interface-audit-report-v1",
        "mask_type_schema": schema_masks,
        "mask_type_runtime": runtime_masks,
        "mask_type_adapter_declared": adapter_declared_masks,
        "mask_type_adapter_outputs": adapter_output_masks,
        "mask_type_mismatches": mask_mismatches,
        "action_type_schema": schema_actions,
        "action_type_adapter_declared": adapter_actions,
        "action_type_adapter_outputs": adapter_output_actions,
        "action_type_mismatches": action_mismatches,
        "absolute_path_violations": absolute_violations,
        "diffsynth_metadata_check": diffsynth_check,
        "qwenvl_export_check": qwenvl_check,
        "recommended_status": "frozen" if frozen else "not_frozen",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote interface audit report to {args.report}")
    return 0 if frozen else 1


if __name__ == "__main__":
    raise SystemExit(main())

