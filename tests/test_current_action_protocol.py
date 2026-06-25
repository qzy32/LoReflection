import json
from pathlib import Path


def test_current_action_sets():
    manifest = json.loads(Path("artifacts/current_interface/manifest.json").read_text(encoding="utf-8"))
    assert manifest["actions"] == ["ADD", "REMOVE", "TRANSLATE", "ROTATE", "SCALE", "REPLACE"]
    assert manifest["semantic_repair4"] == ["ADD", "REMOVE", "TRANSLATE", "REPLACE"]
    assert manifest["parametric_update"] == ["ROTATE", "SCALE"]


def test_current_handoff_examples_use_canonical_actions_only():
    path = Path("outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl")
    plans = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        plans.append(json.loads(row["conversations"][-1]["value"]))
    assert {p["action_type"] for p in plans} == {"ADD", "REMOVE", "TRANSLATE", "ROTATE", "SCALE", "REPLACE"}
    old_aliases = {"IN" + "SERT", "DE" + "LETE", "MO" + "VE", "RE" + "SIZE", "UPDATE" + "_YAW", "UPDATE" + "_SIZE"}
    assert not ({p["action_type"] for p in plans} & old_aliases)
