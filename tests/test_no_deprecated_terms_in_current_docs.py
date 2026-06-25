from pathlib import Path


CURRENT_PATHS = [
    Path("docs/CURRENT_PROJECT_STATE.md"),
    Path("docs/C12_SANITIZER_CURRENT_PLAN.md"),
    Path("outputs/current_vlm_planner_handoff"),
    Path("artifacts/current_interface"),
]


def test_no_deprecated_execution_terms_in_current_files():
    banned = [
        "semantic-repair" + "5",
        "semantic_repair" + "5",
        "semantic-repair" + "6",
        "semantic_repair" + "6",
        "repair" + "6",
        "semantic" + "_inpaint",
        "hy" + "brid",
        "apm" + "_attribute_update",
    ]
    hits = []
    for root in CURRENT_PATHS:
        paths = root.rglob("*") if root.is_dir() else [root]
        for path in paths:
            if path.is_file() and path.suffix in {".md", ".json", ".jsonl"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for term in banned:
                    if term in text:
                        hits.append((str(path), term))
    assert hits == []


def test_current_sft_has_no_old_top_level_aliases():
    text = Path("outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl").read_text(encoding="utf-8")
    for term in ['"IN' + 'SERT"', '"DE' + 'LETE"', '"MO' + 'VE"', '"RE' + 'SIZE"', '"UPDATE' + '_YAW"', '"UPDATE' + '_SIZE"']:
        assert term not in text
