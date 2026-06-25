from pathlib import Path


DOCS = [
    Path("README.md"),
    Path("docs/CURRENT_PROJECT_STATE.md"),
    Path("docs/START_HERE.md"),
    Path("PROGRESS.md"),
]

FORBIDDEN_MAINLINE_SNIPPETS = [
    "-> RepairPlan",
    "VLM Correction Planner",
    "semantic_repair4:",
    "blockwise_controlnet_image =",
    "blockwise_controlnet_inpaint_mask =",
    "Only semantic_repair4 actions enter",
]


def test_entry_docs_do_not_present_repairplan_as_mainline():
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_MAINLINE_SNIPPETS:
            assert snippet not in text, f"{path} still presents old route snippet as current: {snippet}"
        assert "StatePatch" in text
        assert "Architecture In-Context" in text

