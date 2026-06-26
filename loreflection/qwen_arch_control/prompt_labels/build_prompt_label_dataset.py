from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from loreflection.qwen_arch_control.prompt_labels.audit_prompt_variants import audit_prompt_label_dataset
from loreflection.qwen_arch_control.prompt_labels.goal_constraint_extractor import assert_no_geometry, build_rich_goal_lostate
from loreflection.qwen_arch_control.prompt_labels.llm_prompt_request_exporter import make_request, write_requests
from loreflection.qwen_arch_control.prompt_labels.scene_fact_extractor import extract_scene_facts
from loreflection.qwen_arch_control.prompt_labels.template_prompt_generator import generate_prompt_variants, prompt_package


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def build_prompt_label_dataset(source_root: Path, output_root: Path, request_path: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "meta").mkdir(exist_ok=True)
    (output_root / "audits").mkdir(exist_ok=True)
    source_rows = list(csv.DictReader((source_root / "metadata.csv").open("r", encoding="utf-8", newline="")))
    variant_rows: dict[str, list[dict[str, str]]] = {"template_minimal": [], "template_functional": [], "template_user_like": []}
    mixed_rows = []
    requests = []
    examples = []
    rich_examples = []
    for row in source_rows:
        sid = row["sample_id"]
        layout = json.loads((source_root / "meta" / f"{sid}_layout.json").read_text(encoding="utf-8"))
        arch = json.loads((source_root / "meta" / f"{sid}_architecture.json").read_text(encoding="utf-8"))
        scene_facts = extract_scene_facts(layout, arch, sid)
        rich_goal = build_rich_goal_lostate(scene_facts, f"meta/{sid}_architecture.json")
        assert_no_geometry(rich_goal)
        variants = generate_prompt_variants(scene_facts)
        _write_json(output_root / "meta" / f"{sid}_scene_facts.json", scene_facts)
        _write_json(output_root / "meta" / f"{sid}_goal_lostate_rich.json", rich_goal)
        _write_json(output_root / "meta" / f"{sid}_prompt_variants.json", variants)
        requests.append(make_request(sid, scene_facts, rich_goal))
        if len(examples) < 5:
            examples.append({"sample_id": sid, **variants})
        if len(rich_examples) < 3:
            rich_examples.append(rich_goal)
        for name, prompt in variants.items():
            package = prompt_package(name, prompt, scene_facts)
            package_path = output_root / "meta" / f"{sid}_{name}_prompt_package.json"
            _write_json(package_path, package)
            out_row = {
                "image": f"../{source_root.name}/{row['image']}",
                "prompt": prompt,
                "context_image": f"../{source_root.name}/{row['context_image']}",
                "sample_id": sid,
                "goal_lostate": f"meta/{sid}_goal_lostate_rich.json",
                "prompt_package": f"meta/{sid}_{name}_prompt_package.json",
                "verifier_refs": f"../{source_root.name}/{row['verifier_refs']}",
            }
            variant_rows[name].append(out_row)
            mixed_rows.append(out_row)
    fieldnames = ["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"]
    for name, rows in variant_rows.items():
        with (output_root / f"metadata_{name}.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader(); writer.writerows(rows)
    with (output_root / "metadata_mixed_template_variants.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(mixed_rows)
    write_requests(request_path, requests)
    audit = audit_prompt_label_dataset(output_root)
    result = {"source_root": str(source_root), "output_root": str(output_root), "num_samples": len(source_rows), "audit": audit, "examples": examples, "rich_goal_examples": rich_examples, "request_path": str(request_path)}
    _write_json(output_root / "audits" / "prompt_label_build_result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--request-path", type=Path, default=Path("data/loreflection_prompt_label_requests/p1_small_metric_v2_prompt_label_requests.jsonl"))
    args = parser.parse_args()
    result = build_prompt_label_dataset(args.source_root, args.output_root, args.request_path)
    print(json.dumps({k: v for k, v in result.items() if k not in {"examples", "rich_goal_examples"}}, ensure_ascii=False, indent=2))
    return 0 if result["audit"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
