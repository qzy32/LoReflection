import copy
import json
from pathlib import Path

import pytest

from tools.validate_current_repairplan import ValidationError, validate_plan


def _plans():
    path = Path("outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl")
    return [json.loads(json.loads(line)["conversations"][-1]["value"]) for line in path.read_text(encoding="utf-8").splitlines()]


def test_examples_validate():
    for plan in _plans():
        validate_plan(plan)


def test_rotate_scale_reject_semantic_repair_fields():
    for action in ["ROTATE", "SCALE"]:
        plan = next(p for p in _plans() if p["action_type"] == action)
        bad = copy.deepcopy(plan)
        bad["execution_mode"] = "semantic_repair"
        bad["mask_spec"] = {"components": []}
        bad["correction_prompt"] = "paint this"
        with pytest.raises(ValidationError):
            validate_plan(bad)


def test_semantic_repair_actions_reject_parametric_mode():
    for action in ["ADD", "REMOVE", "TRANSLATE", "REPLACE"]:
        plan = next(p for p in _plans() if p["action_type"] == action)
        bad = copy.deepcopy(plan)
        bad["execution_mode"] = "parametric_update"
        with pytest.raises(ValidationError):
            validate_plan(bad)


def test_action_count_delta_constraints():
    add = next(p for p in _plans() if p["action_type"] == "ADD")
    bad_add = copy.deepcopy(add)
    bad_add["target_state_delta"]["target_count_delta"] = 0
    with pytest.raises(ValidationError):
        validate_plan(bad_add)

    remove = next(p for p in _plans() if p["action_type"] == "REMOVE")
    bad_remove = copy.deepcopy(remove)
    bad_remove["target_state_delta"]["target_count_delta"] = 0
    with pytest.raises(ValidationError):
        validate_plan(bad_remove)


def test_translate_requires_old_new_and_disconnected_mask():
    plan = next(p for p in _plans() if p["action_type"] == "TRANSLATE")

    missing_new = copy.deepcopy(plan)
    missing_new["mask_spec"]["components"] = [
        c for c in missing_new["mask_spec"]["components"] if c["component_role"] != "new_region"
    ]
    with pytest.raises(ValidationError):
        validate_plan(missing_new)

    connected = copy.deepcopy(plan)
    connected["mask_spec"]["allow_disconnected"] = False
    with pytest.raises(ValidationError):
        validate_plan(connected)


def test_replace_requires_source_and_target_regions():
    plan = next(p for p in _plans() if p["action_type"] == "REPLACE")
    bad = copy.deepcopy(plan)
    bad["mask_spec"]["components"] = [
        c for c in bad["mask_spec"]["components"] if c["component_role"] != "source_region"
    ]
    with pytest.raises(ValidationError):
        validate_plan(bad)


def test_rotate_scale_reject_mask_or_prompt_individually():
    rotate = next(p for p in _plans() if p["action_type"] == "ROTATE")
    with_mask = copy.deepcopy(rotate)
    with_mask["mask_spec"] = next(p for p in _plans() if p["action_type"] == "ADD")["mask_spec"]
    with pytest.raises(ValidationError):
        validate_plan(with_mask)

    scale = next(p for p in _plans() if p["action_type"] == "SCALE")
    with_prompt = copy.deepcopy(scale)
    with_prompt["correction_prompt"] = "paint something"
    with pytest.raises(ValidationError):
        validate_plan(with_prompt)
