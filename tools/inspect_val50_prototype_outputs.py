#!/usr/bin/env python
"""Inspect a bounded real val50 prototype package.

The inspector checks structure, relative paths, JSON readability, PNG
readability, and minimal entity counts. Warnings are allowed; missing files or
unreadable core artifacts are failures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ABSOLUTE_PATH_MARKERS = ("C:/", "C:\\", "/Users/", "/home/", "/mnt/")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_png(path: Path) -> bool:
    try:
        return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def has_absolute_marker(value: Any) -> bool:
    return any(marker in json.dumps(value, ensure_ascii=False) for marker in ABSOLUTE_PATH_MARKERS)


def check_relative_path(package_root: Path, rel_path: str, failures: list[str]) -> Path:
    if not rel_path or Path(rel_path).is_absolute() or any(marker in rel_path for marker in ABSOLUTE_PATH_MARKERS):
        failures.append(f"Path is not package-relative: {rel_path}")
    path = package_root / rel_path
    if not path.exists():
        failures.append(f"Missing path: {rel_path}")
    return path


def inspect_package(package_root: Path, strict: bool) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    manifest_path = package_root / "manifest.json"
    if not manifest_path.exists():
        failures.append("Missing manifest.json")
        manifest: dict[str, Any] = {}
    else:
        try:
            manifest = load_json(manifest_path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"manifest.json is not readable JSON: {exc}")
            manifest = {}

    if has_absolute_marker(manifest.get("samples", [])):
        failures.append("Manifest sample entries contain forbidden absolute path markers.")

    samples = manifest.get("samples", [])
    if not isinstance(samples, list):
        failures.append("manifest.samples must be a list.")
        samples = []

    entities_per_scene: dict[str, int] = {}
    lamp_entities_per_scene: dict[str, int] = {}
    architecture_condition_count = 0
    per_scene_warnings: dict[str, list[str]] = {}
    for sample in samples:
        if not isinstance(sample, dict):
            failures.append("Found non-object sample entry.")
            continue
        scene_id = str(sample.get("scene_id", "unknown"))
        required_keys = ["source_json", "architecture_json", "semantic_layout", "observed_lostate", "preview"]
        if strict:
            required_keys.append("architecture_condition")
        for key in required_keys:
            if key not in sample:
                failures.append(f"{scene_id}: missing manifest field {key}")
                continue
            path = check_relative_path(package_root, str(sample[key]), failures)
            if key.endswith("json") or key in {"architecture_json", "observed_lostate", "source_json"}:
                if path.exists():
                    try:
                        load_json(path)
                    except Exception as exc:  # noqa: BLE001
                        failures.append(f"{scene_id}: {key} is unreadable JSON: {exc}")
            if key in {"semantic_layout", "preview", "architecture_condition"} and path.exists() and not is_png(path):
                failures.append(f"{scene_id}: {key} is not a PNG: {sample[key]}")
            if key == "architecture_condition" and path.exists() and is_png(path):
                architecture_condition_count += 1

        observed_path = package_root / str(sample.get("observed_lostate", ""))
        if observed_path.exists():
            observed = load_json(observed_path)
            entities = observed.get("furniture_instances", [])
            count = len(entities) if isinstance(entities, list) else 0
            entities_per_scene[scene_id] = count
            lamp_entities_per_scene[scene_id] = sum(1 for item in entities if isinstance(item, dict) and item.get("is_lamp"))
            if count < 3:
                failures.append(f"{scene_id}: expected at least 3 furniture entities, found {count}")
            if observed.get("warnings"):
                per_scene_warnings[scene_id] = observed.get("warnings", [])

    jid_report = package_root / "category_mapping_v1" / "jid_mapping_report.json"
    if not jid_report.exists():
        failures.append("Missing category_mapping_v1/jid_mapping_report.json")
    else:
        try:
            load_json(jid_report)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"jid_mapping_report.json is unreadable: {exc}")

    contact_sheet = package_root / "preview" / "contact_sheet.png"
    if not contact_sheet.exists():
        failures.append("Missing preview/contact_sheet.png")
    elif not is_png(contact_sheet):
        failures.append("preview/contact_sheet.png is not a PNG")

    report = {
        "schema_version": "real-val50-prototype-audit-report-v1",
        "package_root": package_root.as_posix(),
        "manifest_exists": manifest_path.exists(),
        "sample_count": len(samples),
        "architecture_condition_count": architecture_condition_count,
        "entities_per_scene": entities_per_scene,
        "lamp_entities_per_scene": lamp_entities_per_scene,
        "warning_scene_count": len(per_scene_warnings),
        "warning_summary": per_scene_warnings,
        "failures": failures,
        "status": "failed" if failures else "passed_with_warnings" if per_scene_warnings else "passed",
    }
    if strict and failures:
        report["strict_failed"] = True
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True, help="Prototype package root.")
    parser.add_argument("--report", type=Path, required=True, help="Audit report output path.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero for structural failures.")
    args = parser.parse_args()

    report = inspect_package(args.package_root, args.strict)
    write_json(args.report, report)
    if report["failures"]:
        print(f"Real val50 prototype inspection failed with {len(report['failures'])} issue(s).")
        for failure in report["failures"]:
            print(f"- {failure}")
        return 1 if args.strict else 0
    print("Real val50 prototype inspection passed.")
    if report["status"] == "passed_with_warnings":
        print(f"Warnings are present for {report['warning_scene_count']} scene(s); see {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
