from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

PROMPT_KEYS = ("prompt_llm_short", "prompt_llm_functional", "prompt_llm_user_like")
FORBIDDEN_REQUEST_KEYS = {
    "center_m", "size_m", "orientation_deg", "bbox_px", "bbox", "metric_transform",
    "source_json_path", "footprint_m", "polygon_px", "polygon_m",
}


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def scrub_forbidden(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: scrub_forbidden(v) for k, v in obj.items() if k not in FORBIDDEN_REQUEST_KEYS}
    if isinstance(obj, list):
        return [scrub_forbidden(v) for v in obj]
    return obj


def _required_items_text(request: dict[str, Any]) -> str:
    user = request.get("user", {}) if isinstance(request, dict) else {}
    facts = user.get("scene_facts", {}) if isinstance(user, dict) else {}
    counts = facts.get("furniture_counts", {}) if isinstance(facts, dict) else {}
    parts = []
    for category, count in counts.items():
        phrase = str(category).replace("_", " ")
        parts.append(f"{count} {phrase}")
    return ", ".join(parts) if parts else "the provided furniture categories"


def build_messages(request: dict[str, Any]) -> list[dict[str, str]]:
    required_items = _required_items_text(request)
    strict_system = (
        "You generate coordinate-free indoor layout instructions. "
        "Do not mention coordinates, sizes, pixels, meters, source paths, hidden IDs, bbox, center, orientation, metric transform, or JSON field names. "
        "Output valid JSON only. Every prompt must start with \"Context_Control.\" "
        "Use only furniture categories provided in the input. Do not invent new furniture categories. "
        "Use the provided furniture category names as human-readable phrases without synonyms."
    )
    user_payload = scrub_forbidden(request.get("user", {}))
    user_text = (
        "Generate three indoor semantic-layout prompts from this structured input. "
        f"Every prompt must explicitly mention all required furniture and counts: {required_items}. "
        "Do not omit any listed furniture category. Do not replace category names with synonyms. "
        "Return exactly this JSON object with string values: "
        "{\"prompt_llm_short\": \"Context_Control. ...\", "
        "\"prompt_llm_functional\": \"Context_Control. ...\", "
        "\"prompt_llm_user_like\": \"Context_Control. ...\"}.\n"
        f"Input JSON:\n{json.dumps(user_payload, ensure_ascii=False, indent=2)}"
    )
    return [{"role": "system", "content": strict_system}, {"role": "user", "content": user_text}]


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start:end + 1])


def normalize_prompt_object(obj: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key in PROMPT_KEYS:
        value = str(obj.get(key, "")).strip()
        if value and not value.startswith("Context_Control."):
            value = "Context_Control. " + value.removeprefix("Context_Control").lstrip(". ")
        out[key] = value
    return out


def load_model(model_path: Path):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return tokenizer, model


def generate_one(tokenizer: Any, model: Any, request: dict[str, Any], args: argparse.Namespace) -> tuple[dict[str, str] | None, str, str | None]:
    messages = build_messages(request)
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    output_ids = model.generate(
        **inputs,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty,
        do_sample=args.temperature > 0,
    )
    generated_ids = output_ids[:, inputs.input_ids.shape[1]:]
    raw = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    try:
        obj = normalize_prompt_object(extract_json_object(raw))
    except Exception as exc:  # noqa: BLE001 - record parse failures for audit.
        return None, raw, str(exc)
    return obj, raw, None


def prompt_package(variant_name: str, prompt: str, sample_id: str) -> dict[str, Any]:
    return {
        "schema_version": "prompt-package-v2-llm",
        "variant_name": variant_name,
        "sample_id": sample_id,
        "compiled_text_prompt": prompt,
        "negative_prompt": "coordinates, pixel values, metric dimensions, hidden ids, source paths, JSON field names",
        "prompt_constraint_refs": ["inside_room", "avoid_overlap", "palette_exact", "use_architecture_condition_image"],
        "verifier_only_constraint_refs": [],
        "constraint_routes": {
            "inside_room": "prompt",
            "avoid_overlap": "prompt",
            "palette_exact": "prompt",
            "use_architecture_condition_image": "prompt",
        },
    }


def build_metadata(output_root: Path, template_root: Path, outputs: list[dict[str, Any]]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "meta").mkdir(exist_ok=True)
    base_rows = {
        row["sample_id"]: row
        for row in csv.DictReader((template_root / "metadata_template_functional.csv").open("r", encoding="utf-8", newline=""))
    }
    fieldnames = ["image", "prompt", "context_image", "sample_id", "goal_lostate", "prompt_package", "verifier_refs"]
    variant_rows = {"llm_short": [], "llm_functional": [], "llm_user_like": []}
    mixed_rows = []
    key_to_variant = {
        "prompt_llm_short": "llm_short",
        "prompt_llm_functional": "llm_functional",
        "prompt_llm_user_like": "llm_user_like",
    }
    for row in outputs:
        if not row.get("parse_ok"):
            continue
        sid = row["sample_id"]
        base = base_rows.get(sid)
        if not base:
            continue
        prompts = row["prompts"]
        goal_src = template_root / base["goal_lostate"]
        goal_dst = output_root / base["goal_lostate"]
        if goal_src.exists() and not goal_dst.exists():
            goal_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(goal_src, goal_dst)
        for prompt_key, variant in key_to_variant.items():
            package_path = output_root / "meta" / f"{sid}_{variant}_prompt_package.json"
            package_path.write_text(json.dumps(prompt_package(variant, prompts[prompt_key], sid), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            out_row = {
                "image": base["image"],
                "prompt": prompts[prompt_key],
                "context_image": base["context_image"],
                "sample_id": sid,
                "goal_lostate": base["goal_lostate"],
                "prompt_package": f"meta/{sid}_{variant}_prompt_package.json",
                "verifier_refs": base["verifier_refs"],
            }
            variant_rows[variant].append(out_row)
            mixed_rows.append(out_row)
    for variant, rows in variant_rows.items():
        path = output_root / f"metadata_{variant}.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader(); writer.writerows(rows)
    with (output_root / "metadata_mixed_llm_variants.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(mixed_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-jsonl", type=Path, required=True)
    parser.add_argument("--template-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--failed-jsonl", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=Path("/wuqingyaoa800/chengjiajia_datas/models/Qwen2.5-7B-Instruct"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--temperature", type=float, default=0.4)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    args = parser.parse_args()

    requests = read_jsonl(args.request_jsonl, args.limit)
    tokenizer, model = load_model(args.model_path)
    outputs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for idx, request in enumerate(requests, start=1):
        sid = request.get("sample_id", f"sample_{idx:04d}")
        prompts, raw, error = generate_one(tokenizer, model, request, args)
        record = {
            "sample_id": sid,
            "model_path": str(args.model_path),
            "parse_ok": prompts is not None,
            "prompts": prompts,
            "raw_response": raw,
            "error": error,
        }
        outputs.append(record)
        if error:
            failures.append({"sample_id": sid, "error": error, "raw_response": raw})
        print(json.dumps({"idx": idx, "sample_id": sid, "parse_ok": prompts is not None}, ensure_ascii=False), flush=True)
    write_jsonl(args.output_jsonl, outputs)
    write_jsonl(args.failed_jsonl, failures)
    build_metadata(args.output_root, args.template_root, outputs)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
