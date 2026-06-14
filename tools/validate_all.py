#!/usr/bin/env python
"""Batch-validate LoReflection JSON artifacts under a data root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    "perturbation-manifest-v1",
    "semlayoutdiff-inspect-report-v1",
    "semlayoutdiff-conversion-report-v1",
    "semlayoutdiff-npy-placeholder-report-v1",
    "editroom-inspect-report-v1",
    "editroom-conversion-report-v1",
    "interface-audit-report-v1",
    "unified-toy-package-v1",
    "unified-package-report-v1",
    "unified-package-validation-report-v1",
    "server-path-check-report-v1",
}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("examples/toy_samples"), help="Directory containing JSON artifacts.")
    parser.add_argument("--schema-dir", type=Path, default=Path("schemas"), help="Directory containing LoReflection schemas.")
    parser.add_argument("--strict", action="store_true", help="Fail on JSON files with unknown schema_version.")
    args = parser.parse_args()

    validators = {}
    failures = 0
    skipped = 0
    for json_path in sorted(args.data_root.rglob("*.json")):
        data = load_json(json_path)
        if isinstance(data, list) and all(isinstance(row, dict) and {"image", "conversations"}.issubset(row) for row in data):
            print(f"[OK] {json_path} -> qwen-vl-sft-format")
            continue
        version = data.get("schema_version") if isinstance(data, dict) else None
        schema_name = SCHEMA_BY_VERSION.get(version)
        if version == "controlnet-repair-manifest-v1":
            schema_name = "controlnet_sample_v1.schema.json"
            if schema_name not in validators:
                validators[schema_name] = Draft202012Validator(load_json(args.schema_dir / schema_name))
            sample_errors = []
            for index, sample in enumerate(data.get("samples", [])):
                sample_errors.extend((index, err) for err in validators[schema_name].iter_errors(sample))
            if sample_errors:
                failures += 1
                print(f"[FAIL] {json_path}")
                for index, err in sample_errors:
                    loc = ".".join(str(p) for p in err.path) or "<root>"
                    print(f"  - samples[{index}].{loc}: {err.message}")
            else:
                print(f"[OK] {json_path} -> controlnet_sample_v1.schema.json samples")
            continue
        if version == "planner-sft-manifest-v1":
            required = {"sample_id", "image", "goal_lostate", "observed_lostate", "loreview", "repairplan"}
            missing = [(idx, sorted(required - set(sample))) for idx, sample in enumerate(data.get("samples", [])) if required - set(sample)]
            if missing:
                failures += 1
                print(f"[FAIL] {json_path}")
                for idx, fields in missing:
                    print(f"  - samples[{idx}] missing {fields}")
            else:
                print(f"[OK] {json_path} -> planner-sft-manifest-v1")
            continue
        if version in MANIFEST_VERSIONS:
            print(f"[OK] {json_path} -> {version}")
            continue
        if not schema_name:
            skipped += 1
            print(f"[SKIP] {json_path} (schema_version={version!r})")
            if args.strict:
                failures += 1
            continue
        if schema_name not in validators:
            validators[schema_name] = Draft202012Validator(load_json(args.schema_dir / schema_name))
        errors = sorted(validators[schema_name].iter_errors(data), key=lambda e: list(e.path))
        if errors:
            failures += 1
            print(f"[FAIL] {json_path}")
            for err in errors:
                loc = ".".join(str(p) for p in err.path) or "<root>"
                print(f"  - {loc}: {err.message}")
        else:
            print(f"[OK] {json_path} -> {schema_name}")

    print(f"Validated with {failures} failure(s), {skipped} skipped file(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
