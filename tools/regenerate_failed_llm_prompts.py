#!/usr/bin/env python
"""Regenerate a small set of failed LLM prompt shard rows.

This calls the LLM-only prompt compiler. It does not use rule fallback and it
refuses to write rows whose prompt package fails strict prompt checks.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loreflection.goal.prompt_compiler import compile_prompt_package
from loreflection.goal.llm_functional_prompt_compiler import build_architecture_summary
from loreflection.goal.prompt_package_validator import PromptCompilerError
from loreflection.semantic_registry import load_registry
from scripts.qwen_arch_control.generate_full_semantic_llm_prompts import TransformersChatClient

REQUIRED_TOKENS = [
    "Context_Control",
    "Architecture_Control",
    "Palette_Control",
    "Active semantic category RGB palette entries",
]
LEAK_PATTERNS = [
    r"\bcenter_m\b",
    r"\bsize_m\b",
    r"\borientation_deg\b",
    r"\bbbox\b",
    r"\bfootprint\b",
    r"\bpixel\b",
    r"\bpx\b",
    r"\bcm\b",
    r"\bmeter\b",
    r"\bcoordinate\b",
    r"\bsource_json_path\b",
]


def read_rows(root: Path) -> dict[str, dict[str, str]]:
    with (root / "metadata.csv").open("r", encoding="utf-8", newline="") as handle:
        return {row["sample_id"]: row for row in csv.DictReader(handle)}


def load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def strict_prompt_errors(obj: dict[str, Any]) -> list[str]:
    prompt = obj.get("compiled_text_prompt") or obj.get("prompt_package", {}).get("compiled_text_prompt", "")
    errors = []
    text = json.dumps(obj, ensure_ascii=False)
    if '"fallback": true' in text or '"fallback_used": true' in text:
        errors.append("fallback_true")
    package = obj.get("prompt_package", {})
    if package.get("prompt_compiler") != "llm_functional":
        errors.append("prompt_compiler_not_llm_functional")
    for token in REQUIRED_TOKENS:
        if token not in prompt:
            errors.append(f"missing_token:{token}")
    for pat in LEAK_PATTERNS:
        if re.search(pat, prompt, flags=re.I):
            errors.append(f"geometry_leak:{pat}")
    report = package.get("validation_report") or {}
    if report.get("status") != "pass":
        errors.append(f"validation_status:{report.get('status')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--sample-id", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=Path("/wuqingyaoa800/chengjiajia_datas/models/Qwen2.5-7B-Instruct"))
    parser.add_argument("--max-new-tokens", type=int, default=420)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()

    rows_by_id = read_rows(args.dataset_root)
    registry = load_registry()
    client = TransformersChatClient(args.model_path, args.max_new_tokens, args.temperature, args.top_p, args.repetition_penalty)
    out_rows = []
    failures = []

    for sid in args.sample_id:
        row = rows_by_id.get(sid)
        if row is None:
            failures.append({"sample_id": sid, "error": "missing_metadata_row"})
            continue
        goal = load_json(args.dataset_root, row["goal_lostate"])
        verifier = load_json(args.dataset_root, row["verifier_refs"])
        architecture = load_json(args.dataset_root, verifier["architecture_json"])
        arch_summary = build_architecture_summary(architecture)
        last_error = None
        for attempt in range(1, args.max_attempts + 1):
            try:
                package = compile_prompt_package(goal, architecture_summary=arch_summary, registry=registry, llm_client=client)
                package["sample_id"] = sid
                package["required_counts"] = goal.get("required_counts") or {}
                package["architecture_summary"] = arch_summary
                obj = {
                    "sample_id": sid,
                    "metadata_prompt_before": row["prompt"],
                    "prompt_package_path": row["prompt_package"],
                    "compiled_text_prompt": package["compiled_text_prompt"],
                    "prompt_package": package,
                    "repair_attempt": attempt,
                }
                errors = strict_prompt_errors(obj)
                if errors:
                    last_error = {"attempt": attempt, "errors": errors, "prompt": package.get("compiled_text_prompt", "")}
                    continue
                out_rows.append(obj)
                last_error = None
                break
            except Exception as exc:
                last_error = {"attempt": attempt, "error": type(exc).__name__, "message": str(exc)}
        if last_error is not None:
            failures.append({"sample_id": sid, "last_error": last_error})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in out_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "requested": len(args.sample_id),
        "written": len(out_rows),
        "failed": len(failures),
        "failures": failures,
        "status": "pass" if len(out_rows) == len(args.sample_id) and not failures else "fail",
        "output": str(args.output),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
