#!/usr/bin/env python
"""Scan tracked project text files for accidentally committed secrets."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


MAX_TEXT_BYTES = 512_000
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "outputs", "data", "models", "checkpoints", "third_party"}
BINARY_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".pt",
    ".pth",
    ".bin",
    ".ckpt",
    ".safetensors",
    ".npy",
    ".npz",
    ".pkl",
}


def sensitive_patterns() -> list[dict[str, str]]:
    return [
        {"label": "password_word", "pattern": "pass" + "word", "severity": "warning"},
        {"label": "chinese_password_word", "pattern": "密" + "码", "severity": "warning"},
        {"label": "known_password_variant_1", "pattern": "qzy" + "240", "severity": "violation"},
        {"label": "known_password_variant_2", "pattern": "qiuziyan" + "240", "severity": "violation"},
        {"label": "public_key_material", "pattern": "ssh" + "-rsa", "severity": "violation"},
        {"label": "openssh_private_key", "pattern": "BEGIN " + "OPENSSH PRIVATE KEY", "severity": "violation"},
        {"label": "rsa_private_key", "pattern": "BEGIN " + "RSA PRIVATE KEY", "severity": "violation"},
        {"label": "local_windows_user_path", "pattern": "C:" + "\\Users\\", "severity": "violation"},
    ]


def is_git_ignored(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    result = subprocess.run(
        ["git", "check-ignore", "-q", rel.as_posix()],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def should_skip(path: Path, root: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.suffix.lower() in BINARY_SUFFIXES:
        return True
    if is_git_ignored(path, root):
        return True
    try:
        return path.stat().st_size > MAX_TEXT_BYTES
    except OSError:
        return True


def scan_file(path: Path, root: Path, patterns: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    violations = []
    warnings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return violations, warnings
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()
    for item in patterns:
        pattern = item["pattern"]
        if pattern.lower() not in text.lower():
            continue
        match = {"file": rel, "label": item["label"]}
        if item["severity"] == "violation":
            violations.append(match)
        else:
            warnings.append(match)
    return violations, warnings


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root to scan.")
    parser.add_argument("--report", type=Path, default=Path("reports/no_secrets_report.json"), help="JSON report path.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on concrete secret violations.")
    args = parser.parse_args()

    root = args.root.resolve()
    patterns = sensitive_patterns()
    checked_files = 0
    violations: list[dict] = []
    warnings: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or should_skip(path, root):
            continue
        checked_files += 1
        file_violations, file_warnings = scan_file(path, root, patterns)
        violations.extend(file_violations)
        warnings.extend(file_warnings)

    report = {"schema_version": "no-secrets-report-v1", "checked_files": checked_files, "violations": violations, "warnings": warnings}
    write_json(args.report, report)
    if violations:
        print(f"Secret check found {len(violations)} violation(s). See {args.report}")
        for violation in violations:
            print(f"- {violation['file']}: {violation['label']}")
        return 1 if args.strict else 0
    print(f"No concrete secret violations found. Checked {checked_files} file(s).")
    if warnings:
        print(f"Warnings: {len(warnings)} general sensitive-word occurrence(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
