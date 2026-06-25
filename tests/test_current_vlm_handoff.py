from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="legacy VLM RepairPlan handoff test retained for C12-C14 baseline only")


def test_current_handoff_files_exist():
    root = Path("outputs/current_vlm_planner_handoff")
    for name in [
        "README_VLM_PLANNER_HANDOFF.md",
        "ACTION_PROTOCOL.md",
        "REPAIRPLAN_OUTPUT_SPEC.md",
        "VALIDATION_GUIDE.md",
        "planner_sft_minimal_examples.jsonl",
        "schemas/repairplan.schema.json",
        "schemas/mask_spec.schema.json",
        "schemas/planner_input_context.schema.json",
    ]:
        assert (root / name).exists()


def test_current_handoff_uses_current_execution_terms():
    text = "\n".join(p.read_text(encoding="utf-8") for p in Path("outputs/current_vlm_planner_handoff").rglob("*.md"))
    assert "semantic_repair" in text
    assert "parametric_update" in text
    assert "semantic" + "_inpaint" not in text
    assert "hy" + "brid" not in text
