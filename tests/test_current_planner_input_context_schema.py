import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


SCHEMA = json.loads(Path("artifacts/current_interface/planner_input_context.schema.json").read_text(encoding="utf-8"))


def _valid_context():
    return {
        "schema_version": "planner-input-context-current",
        "task_tag": "[CORRECTION_PLANNING]",
        "image_refs": {"current_semantic_layout": "current.png"},
        "architecture_summary": {"room_type": "bedroom"},
        "goal_lostate": {"needs": ["bed"]},
        "observed_lostate": {"instances": ["bed_1"]},
        "loreview": {"issues": ["issue_1"]},
        "semantic_registry_ref": "artifacts/current_interface/repairplan.schema.json",
        "palette_ref": "artifacts/semantic_registry_v2/palette.json",
        "allowed_actions": ["ADD", "REMOVE", "TRANSLATE", "ROTATE", "SCALE", "REPLACE"],
        "execution_routing": {
            "semantic_repair4": ["ADD", "REMOVE", "TRANSLATE", "REPLACE"],
            "parametric_update": ["ROTATE", "SCALE"],
        },
        "output_instruction": "Return one RepairPlan JSON only.",
    }


def _validate(data):
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(data), key=lambda error: list(error.path))
    if errors:
        raise AssertionError(errors[0].message)


def test_valid_planner_input_context_passes():
    _validate(_valid_context())


def test_missing_loreview_fails():
    data = _valid_context()
    data.pop("loreview")
    with pytest.raises(AssertionError):
        _validate(data)


def test_empty_goal_lostate_fails():
    data = copy.deepcopy(_valid_context())
    data["goal_lostate"] = {}
    with pytest.raises(AssertionError):
        _validate(data)


def test_empty_registry_ref_fails():
    data = _valid_context()
    data["semantic_registry_ref"] = ""
    with pytest.raises(AssertionError):
        _validate(data)
