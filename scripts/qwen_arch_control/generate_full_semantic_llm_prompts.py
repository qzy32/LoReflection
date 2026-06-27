#!/usr/bin/env python
"""Generate constrained LLM prompts for full_semantic_compiled_main metadata."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from loreflection.goal.prompt_compiler import compile_prompt_package
from loreflection.goal.prompt_compiler_llm import SYSTEM_PROMPT, build_architecture_summary
from loreflection.semantic_registry import load_registry


class TransformersChatClient:
    def __init__(self, model_path: Path, max_new_tokens: int, temperature: float, top_p: float, repetition_penalty: float):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(str(model_path), torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
        self.model.eval()
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty

    def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the JSON prompt package for this Goal LoState payload.\n" + json.dumps(user_payload, ensure_ascii=False, indent=2)},
        ]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
            do_sample=self.temperature > 0,
        )
        generated_ids = output_ids[:, inputs.input_ids.shape[1]:]
        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


def read_rows(root: Path) -> list[dict[str, str]]:
    return list(csv.DictReader((root / "metadata.csv").open("r", encoding="utf-8", newline="")))


def load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def generate_shard(args: argparse.Namespace) -> int:
    root = args.dataset_root
    rows = read_rows(root)
    shard_rows = [row for idx, row in enumerate(rows) if idx % args.num_shards == args.shard_index]
    registry = load_registry()
    client = TransformersChatClient(args.model_path, args.max_new_tokens, args.temperature, args.top_p, args.repetition_penalty)
    out_rows = []
    for local_idx, row in enumerate(shard_rows, start=1):
        sid = row["sample_id"]
        goal = load_json(root, row["goal_lostate"])
        verifier = load_json(root, row["verifier_refs"])
        architecture = load_json(root, verifier["architecture_json"])
        arch_summary = build_architecture_summary(architecture)
        package = compile_prompt_package(goal, architecture_summary=arch_summary, registry=registry, llm_client=client, mode="llm_with_rule_fallback")
        package["sample_id"] = sid
        package["required_counts"] = goal.get("required_counts") or {}
        package["architecture_summary"] = arch_summary
        out_rows.append({
            "sample_id": sid,
            "metadata_prompt_before": row["prompt"],
            "prompt_package_path": row["prompt_package"],
            "compiled_text_prompt": package["compiled_text_prompt"],
            "prompt_package": package,
        })
        if local_idx % args.flush_every == 0:
            write_jsonl(args.output_jsonl, out_rows)
        print(json.dumps({"shard": args.shard_index, "idx": local_idx, "sample_id": sid, "fallback": package.get("llm_prompt_compiler_report", {}).get("fallback_used")}, ensure_ascii=False), flush=True)
    write_jsonl(args.output_jsonl, out_rows)
    return 0


def apply_shards(args: argparse.Namespace) -> int:
    root = args.dataset_root
    rows = read_rows(root)
    by_id = {}
    for path in sorted(args.shard_dir.glob("shard_*_of_*.jsonl")):
        for obj in iter_jsonl(path):
            by_id[obj["sample_id"]] = obj
    missing = [row["sample_id"] for row in rows if row["sample_id"] not in by_id]
    if missing:
        raise RuntimeError(f"Missing LLM prompt rows: {len(missing)}; first={missing[:5]}")
    new_rows = []
    used_llm = fallback = 0
    for row in rows:
        obj = by_id[row["sample_id"]]
        package = obj["prompt_package"]
        report = package.get("llm_prompt_compiler_report") or {}
        used_llm += int(bool(report.get("used_llm")))
        fallback += int(bool(report.get("fallback_used")))
        pkg_path = root / row["prompt_package"]
        pkg_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        new_row = dict(row)
        new_row["prompt"] = package["compiled_text_prompt"]
        new_rows.append(new_row)
    with (root / "metadata.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"])
        writer.writeheader(); writer.writerows(new_rows)
    summary = {"metadata_rows": len(new_rows), "used_llm": used_llm, "fallback_used": fallback, "fallback_rate": fallback / len(new_rows) if new_rows else 0.0, "shard_dir": str(args.shard_dir)}
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("generate-shard")
    gen.add_argument("--dataset-root", type=Path, required=True)
    gen.add_argument("--model-path", type=Path, default=Path("/wuqingyaoa800/chengjiajia_datas/models/Qwen2.5-7B-Instruct"))
    gen.add_argument("--num-shards", type=int, required=True)
    gen.add_argument("--shard-index", type=int, required=True)
    gen.add_argument("--output-jsonl", type=Path, required=True)
    gen.add_argument("--max-new-tokens", type=int, default=320)
    gen.add_argument("--temperature", type=float, default=0.2)
    gen.add_argument("--top-p", type=float, default=0.9)
    gen.add_argument("--repetition-penalty", type=float, default=1.05)
    gen.add_argument("--flush-every", type=int, default=10)
    app = sub.add_parser("apply-shards")
    app.add_argument("--dataset-root", type=Path, required=True)
    app.add_argument("--shard-dir", type=Path, required=True)
    app.add_argument("--summary-json", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "generate-shard":
        return generate_shard(args)
    if args.cmd == "apply-shards":
        return apply_shards(args)
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
