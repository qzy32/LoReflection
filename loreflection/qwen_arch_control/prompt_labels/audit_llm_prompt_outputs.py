from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.audit_prompt_geometry_leakage import find_leaks

PROMPT_KEYS = ("prompt_llm_short", "prompt_llm_functional", "prompt_llm_user_like")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _request_index(request_jsonl: Path | None) -> dict[str, dict[str, Any]]:
    if not request_jsonl:
        return {}
    return {row.get("sample_id", ""): row for row in _read_jsonl(request_jsonl)}


def _allowed_categories(req: dict[str, Any]) -> set[str]:
    user = req.get("user", {}) if isinstance(req, dict) else {}
    goal = user.get("goal_lostate_rich_without_geometry", {}) if isinstance(user, dict) else {}
    slots = goal.get("furniture_slots", []) if isinstance(goal, dict) else []
    cats = {str(slot.get("category", "")) for slot in slots if slot.get("category")}
    facts = user.get("scene_facts", {}) if isinstance(user, dict) else {}
    counts = facts.get("furniture_counts", {}) if isinstance(facts, dict) else {}
    cats.update(str(cat) for cat in counts.keys())
    return cats


def _all_known_categories(requests: dict[str, dict[str, Any]]) -> set[str]:
    cats: set[str] = set()
    for req in requests.values():
        cats.update(_allowed_categories(req))
    return cats


def _normalize_phrase(text: str) -> str:
    lowered = text.lower().replace("_", " ")
    lowered = lowered.replace("'", "").replace("-", " ")
    return " ".join(lowered.split())


def _contains_category(text: str, category: str) -> bool:
    phrase = _normalize_phrase(category)
    haystack = _normalize_phrase(text)
    import re
    words = phrase.split()
    if not words:
        return False
    last = re.escape(words[-1]) + r"(?:s|es)?"
    pattern = r"\s+".join(re.escape(word) for word in words[:-1] + ["__LAST__"])
    pattern = pattern.replace(re.escape("__LAST__"), last)
    return bool(re.search(r"(^|\W)" + pattern + r"($|\W)", haystack))


def _category_overlaps_allowed(category: str, allowed: set[str]) -> bool:
    phrase = _normalize_phrase(category)
    for item in allowed:
        allowed_phrase = _normalize_phrase(item)
        if phrase == allowed_phrase or phrase in allowed_phrase or allowed_phrase in phrase:
            return True
    return False


def _valid_prompt_object(obj: Any) -> bool:
    return isinstance(obj, dict) and all(isinstance(obj.get(key), str) and obj.get(key, "").strip() for key in PROMPT_KEYS)


def audit_llm_prompt_outputs(
    output_jsonl: Path,
    request_jsonl: Path | None = None,
    output: Path | None = None,
    expected_count: int | None = None,
) -> dict[str, Any]:
    rows = _read_jsonl(output_jsonl)
    requests = _request_index(request_jsonl)
    known_categories = _all_known_categories(requests)
    parse_ok = []
    starts = []
    leaks = []
    coverage = []
    unknown_terms = []
    invented = []
    empty = []
    duplicates = []

    for row in rows:
        prompts = row.get("prompts")
        ok = bool(row.get("parse_ok")) and _valid_prompt_object(prompts)
        parse_ok.append(ok)
        if not ok:
            for _ in PROMPT_KEYS:
                starts.append(False); leaks.append(True); coverage.append(False); unknown_terms.append(False); invented.append(False); empty.append(True)
            duplicates.append(False)
            continue
        texts = [str(prompts[key]).strip() for key in PROMPT_KEYS]
        duplicates.append(len(set(texts)) < len(texts))
        allowed = _allowed_categories(requests.get(row.get("sample_id", ""), {}))
        for text in texts:
            starts.append(text.startswith("Context_Control."))
            leaks.append(bool(find_leaks(text)))
            empty.append(not bool(text))
            unknown_terms.append("unknown" in text.lower())
            coverage.append(all(_contains_category(text, cat) for cat in allowed))
            other_known = {cat for cat in known_categories - allowed if not _category_overlaps_allowed(cat, allowed)}
            invented.append(any(_contains_category(text, cat) for cat in other_known))

    n_rows = max(1, len(rows))
    n_prompts = max(1, len(starts))
    report = {
        "num_samples": len(rows),
        "json_parse_success_rate": sum(parse_ok) / n_rows,
        "starts_with_context_control_rate": sum(starts) / n_prompts,
        "coordinate_leakage_rate": sum(leaks) / n_prompts,
        "required_slot_coverage_rate": sum(coverage) / n_prompts,
        "unknown_category_term_rate": sum(unknown_terms) / n_prompts,
        "invented_category_rate": sum(invented) / n_prompts,
        "empty_prompt_rate": sum(empty) / n_prompts,
        "duplicate_prompt_rate": sum(duplicates) / max(1, len(duplicates)),
        "llm_actual_generation_used": any(row.get("model_path") for row in rows),
        "expected_count": expected_count,
    }
    if expected_count is not None:
        report["count_matches_expected"] = len(rows) == expected_count
    if expected_count is not None and expected_count <= 20:
        passed = (
            report["num_samples"] == expected_count
            and report["json_parse_success_rate"] >= 0.95
            and report["starts_with_context_control_rate"] == 1.0
            and report["coordinate_leakage_rate"] == 0.0
            and report["required_slot_coverage_rate"] >= 0.95
            and report["invented_category_rate"] == 0.0
            and report["empty_prompt_rate"] == 0.0
        )
    else:
        target_count_ok = True if expected_count is None else report["num_samples"] == expected_count
        passed = (
            target_count_ok
            and report["json_parse_success_rate"] >= 0.98
            and report["starts_with_context_control_rate"] == 1.0
            and report["coordinate_leakage_rate"] == 0.0
            and report["required_slot_coverage_rate"] >= 0.95
            and report["invented_category_rate"] <= 0.01
            and report["empty_prompt_rate"] == 0.0
        )
    report["status"] = "pass" if passed else "fail"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--request-jsonl", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args()
    report = audit_llm_prompt_outputs(args.output_jsonl, args.request_jsonl, args.output, args.expected_count)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
