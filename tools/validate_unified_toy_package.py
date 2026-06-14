#!/usr/bin/env python
"""Validate a unified LoReflection toy package.

This checker verifies the toy-level package layout that mirrors future
val50 / 1k server artifacts. It validates known JSON schema artifacts,
checks package-relative paths, confirms Qwen-VL and DiffSynth export
formats, and rejects local absolute path leaks.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_BY_VERSION = {
    "architecture-v1": "architecture_v1.schema.json",
    "goal-lostate-v1": "goal_lostate_v1.schema.json",
    "observed-lostate-v1": "observed_lostate_v1.schema.json",
    "prompt-package-v1": "prompt_package_v1.schema.json",
    "loreview-v1": "loreview_v1.schema.json",
    "repairplan-v1": "repairplan_v1.schema.json",
    "mask-spec-v1": "mask_spec_v1.schema.json",
    "controlnet-sample-v1": "controlnet_sample_v1.schema.json",
    "eval-representation-v1": "eval_representation_v1.schema.json",
}

MANIFEST_VERSIONS = {
    "controlnet-repair-manifest-v1",
    "planner-sft-manifest-v1",
    "unified-toy-package-v1",
    "unified-package-report-v1",
    "unified-package-validation-report-v1",
}

ABSOLUTE_PATH_MARKERS = ("C:/", "C:\\", "/Users/", "/home/", "/mnt/")
DIFFSYNTH_FIELDS = {"image", "blockwise_controlnet_image", "blockwise_controlnet_inpaint_mask", "prompt"}
CONTROLNET_PATH_FIELDS = ("control_image", "control_mask", "target_image", "repairplan_path")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_qwenvl_list(data: Any) -> bool:
    if not isinstance(data, list):
        return False
    return all(isinstance(row, dict) and {"image", "conversations"}.issubset(row) for row in data)


def is_relative_safe(value: str) -> bool:
    path = Path(value)
    if path.is_absolute():
        return False
    return not any(marker in value for marker in ABSOLUTE_PATH_MARKERS)


def scan_absolute_path_markers(package_root: Path) -> list[dict[str, str]]:
    violations = []
    for path in sorted(list(package_root.rglob("*.json")) + list(package_root.rglob("*.csv"))):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in ABSOLUTE_PATH_MARKERS:
            if marker in text:
                violations.append({"path": path.as_posix(), "marker": marker})
    return violations


def validate_json_artifacts(package_root: Path, schema_dir: Path, strict: bool) -> list[str]:
    errors: list[str] = []
    validators: dict[str, Draft202012Validator] = {}
    for json_path in sorted(package_root.rglob("*.json")):
        data = load_json(json_path)
        if is_qwenvl_list(data):
            continue
        version = data.get("schema_version") if isinstance(data, dict) else None
        if version == "controlnet-repair-manifest-v1":
            schema_name = "controlnet_sample_v1.schema.json"
            validators.setdefault(schema_name, Draft202012Validator(load_json(schema_dir / schema_name)))
            for index, sample in enumerate(data.get("samples", [])):
                for err in validators[schema_name].iter_errors(sample):
                    loc = ".".join(str(p) for p in err.path) or "<root>"
                    errors.append(f"{json_path}: samples[{index}].{loc}: {err.message}")
            continue
        if version in MANIFEST_VERSIONS:
            continue
        schema_name = SCHEMA_BY_VERSION.get(version)
        if not schema_name:
            if strict:
                errors.append(f"{json_path}: unknown schema_version={version!r}")
            continue
        validators.setdefault(schema_name, Draft202012Validator(load_json(schema_dir / schema_name)))
        for err in sorted(validators[schema_name].iter_errors(data), key=lambda e: list(e.path)):
            loc = ".".join(str(p) for p in err.path) or "<root>"
            errors.append(f"{json_path}: {loc}: {err.message}")
    return errors


def check_package_manifest(package_root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    manifest_path = package_root / "package_manifest.json"
    if not manifest_path.exists():
        return None, [f"Missing {manifest_path}"]
    manifest = load_json(manifest_path)
    for index, sample in enumerate(manifest.get("samples", [])):
        for key, value in sample.items():
            if not isinstance(value, str):
                continue
            if key in {"source", "room_type", "sample_id"}:
                continue
            if not is_relative_safe(value):
                errors.append(f"package_manifest samples[{index}].{key} is not a safe relative path: {value}")
                continue
            if not (package_root / value).exists():
                errors.append(f"package_manifest samples[{index}].{key} missing file: {value}")
    return manifest, errors


def check_qwenvl(package_root: Path) -> dict[str, Any]:
    path = package_root / "planner_sft_v1" / "qwenvl_sft.json"
    result: dict[str, Any] = {"path": path.as_posix(), "exists": path.exists(), "passed": False, "errors": []}
    if not path.exists():
        result["errors"].append("missing qwenvl_sft.json")
        return result
    data = load_json(path)
    if not isinstance(data, list):
        result["errors"].append("Qwen-VL export must be a list")
        return result
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            result["errors"].append(f"row {index} is not an object")
            continue
        image = row.get("image")
        if not isinstance(image, str) or not is_relative_safe(image):
            result["errors"].append(f"row {index} image path is not relative/safe")
        elif not (package_root / image).exists():
            result["errors"].append(f"row {index} image missing: {image}")
        conv = row.get("conversations")
        if not isinstance(conv, list) or len(conv) < 2:
            result["errors"].append(f"row {index} conversations must contain at least two turns")
            continue
        if conv[0].get("from") != "human" or "[CORRECTION_PLANNING" not in conv[0].get("value", ""):
            result["errors"].append(f"row {index} human turn missing correction planning task token")
        if conv[1].get("from") != "gpt":
            result["errors"].append(f"row {index} assistant turn must use from=gpt")
        else:
            try:
                json.loads(conv[1].get("value", ""))
            except json.JSONDecodeError as exc:
                result["errors"].append(f"row {index} assistant value is not strict JSON: {exc}")
    result["passed"] = not result["errors"]
    return result


def check_diffsynth_metadata(package_root: Path) -> dict[str, Any]:
    path = package_root / "diffsynth_inpaint_v1" / "metadata.csv"
    result: dict[str, Any] = {"path": path.as_posix(), "exists": path.exists(), "passed": False, "rows": 0, "errors": []}
    if not path.exists():
        result["errors"].append("missing metadata.csv")
        return result
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        missing = sorted(DIFFSYNTH_FIELDS - fields)
        if missing:
            result["errors"].append(f"metadata.csv missing fields: {missing}")
        for index, row in enumerate(reader):
            result["rows"] += 1
            for field in DIFFSYNTH_FIELDS - {"prompt"}:
                value = row.get(field, "")
                if not is_relative_safe(value):
                    result["errors"].append(f"row {index} {field} is not a safe relative path: {value}")
                elif not (package_root / value).exists():
                    result["errors"].append(f"row {index} {field} missing file: {value}")
            if not row.get("prompt"):
                result["errors"].append(f"row {index} prompt is empty")
    result["passed"] = not result["errors"]
    return result


def check_controlnet_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "controlnet_repair_v1" / "train.json"
    result: dict[str, Any] = {"path": path.as_posix(), "exists": path.exists(), "passed": False, "samples": 0, "errors": []}
    if not path.exists():
        result["errors"].append("missing controlnet_repair_v1/train.json")
        return result
    data = load_json(path)
    for index, sample in enumerate(data.get("samples", [])):
        result["samples"] += 1
        for field in CONTROLNET_PATH_FIELDS:
            value = sample.get(field)
            if not isinstance(value, str) or not is_relative_safe(value):
                result["errors"].append(f"samples[{index}].{field} is not a safe relative path: {value}")
            elif not (package_root / value).exists():
                result["errors"].append(f"samples[{index}].{field} missing file: {value}")
    result["passed"] = not result["errors"]
    return result


def check_pngs(package_root: Path) -> list[str]:
    errors: list[str] = []
    for directory in ["masks", "images", "targets"]:
        base = package_root / directory
        if not base.exists():
            errors.append(f"missing directory: {directory}")
            continue
        for path in sorted(base.glob("*")):
            if path.is_file() and path.suffix.lower() != ".png" and path.parent.name != "specs":
                errors.append(f"{path} is not a PNG")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True, help="Unified toy package root.")
    parser.add_argument("--schema-dir", type=Path, default=Path("schemas"), help="LoReflection schema directory.")
    parser.add_argument("--strict", action="store_true", help="Fail on unknown schema versions.")
    parser.add_argument("--report", type=Path, required=True, help="Validation report path.")
    args = parser.parse_args()

    errors: list[str] = []
    manifest, manifest_errors = check_package_manifest(args.package_root)
    errors.extend(manifest_errors)
    errors.extend(validate_json_artifacts(args.package_root, args.schema_dir, args.strict))
    errors.extend(check_pngs(args.package_root))

    qwenvl = check_qwenvl(args.package_root)
    diffsynth = check_diffsynth_metadata(args.package_root)
    controlnet = check_controlnet_manifest(args.package_root)
    for result in [qwenvl, diffsynth, controlnet]:
        errors.extend(result.get("errors", []))
    absolute_path_violations = scan_absolute_path_markers(args.package_root)
    for violation in absolute_path_violations:
        errors.append(f"absolute path marker {violation['marker']} in {violation['path']}")

    report = {
        "schema_version": "unified-package-validation-report-v1",
        "package_root": args.package_root.as_posix(),
        "package_manifest_found": manifest is not None,
        "artifact_counts": manifest.get("artifact_counts", {}) if isinstance(manifest, dict) else {},
        "qwenvl_sft_check": qwenvl,
        "diffsynth_metadata_check": diffsynth,
        "controlnet_repair_check": controlnet,
        "absolute_path_violations": absolute_path_violations,
        "errors": errors,
        "passed": not errors,
    }
    write_json(args.report, report)
    if errors:
        print(f"Unified toy package validation failed with {len(errors)} error(s). See {args.report}")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Unified toy package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
