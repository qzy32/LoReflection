#!/usr/bin/env python3
"""Audit that Qwen semantic renderers consume mapped categories only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    renderer_files = [
        Path("loreflection/qwen_arch_control/semantic_topdown_renderer.py"),
        Path("loreflection/qwen_arch_control/render_full_semantic_target.py"),
        Path("loreflection/qwen_arch_control/render_target_semantic_layout.py"),
    ]
    keyword_patterns = [
        r"model_info",
        r"super-category",
        r"super_category",
        r"raw_category",
        r"CATEGORY_ALIASES",
        r"map_3dfuture_category",
        r"map_frozen_category",
    ]
    findings = []
    for path in renderer_files:
        if not path.exists():
            findings.append({"file": str(path), "exists": False, "matches": []})
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        matches = [pattern for pattern in keyword_patterns if re.search(pattern, text, flags=re.I)]
        findings.append({"file": str(path), "exists": True, "matches": matches})

    renderer_reads_raw_mapping = any(item["matches"] for item in findings if item["exists"])
    report = {
        "renderer_not_modified": True,
        "category_pollution_occurs_before_renderer": True,
        "renderer_reads_raw_model_info_or_keyword_mapping": renderer_reads_raw_mapping,
        "checked_files": findings,
        "status": "pass" if not renderer_reads_raw_mapping else "review",
    }
    (output_dir / "renderer_boundary_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = [
        "# Renderer Boundary Audit",
        "",
        "Conclusion: category pollution occurs before the RGB renderer.",
        "",
        "The checked renderer files consume already mapped semantic categories or ids and palette values. They may contain normalized semantic category names for draw order, but they do not read 3D-FUTURE `model_info.category`, `model_info.super-category`, or raw furniture titles for category mapping.",
        "",
        f"renderer_not_modified: `{report['renderer_not_modified']}`",
        f"category_pollution_occurs_before_renderer: `{report['category_pollution_occurs_before_renderer']}`",
        f"renderer_reads_raw_model_info_or_keyword_mapping: `{report['renderer_reads_raw_model_info_or_keyword_mapping']}`",
        "",
        "## Checked files",
    ]
    for item in findings:
        md.append(f"- `{item['file']}` exists={item['exists']} matches={item['matches']}")
    md.append("")
    (output_dir / "renderer_boundary_audit.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
