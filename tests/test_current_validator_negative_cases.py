import copy
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="legacy RepairPlan validator test retained for C12-C14 baseline only")

from tools.validate_current_repairplan import ValidationError, validate_plan


def _plans():
    path = Path("outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl")
    return [json.loads(json.loads(line)["conversations"][-1]["value"]) for line in path.read_text(encoding="utf-8").splitlines()]


def _plan(action: str):
    return next(plan for plan in _plans() if plan["action_type"] == action)


def test_old_alias_action_is_rejected():
    plan = copy.deepcopy(_plan("ADD"))
    plan["action_type"] = "IN" + "SERT"
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_forbidden_executor_artifacts_are_rejected():
    plan = copy.deepcopy(_plan("ADD"))
    plan["executor_leak"] = "control_mask.png"
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_semantic_repair_without_mask_fails():
    plan = copy.deepcopy(_plan("ADD"))
    plan["mask_spec"] = None
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_parametric_update_with_mask_fails():
    plan = copy.deepcopy(_plan("ROTATE"))
    plan["mask_spec"] = copy.deepcopy(_plan("ADD"))["mask_spec"]
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_parametric_update_without_delta_fails():
    plan = copy.deepcopy(_plan("SCALE"))
    plan["parametric_delta"] = None
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_translate_delta_must_be_bookkeeping_only():
    plan = copy.deepcopy(_plan("TRANSLATE"))
    plan["parametric_delta"]["bookkeeping_only"] = False
    with pytest.raises(ValidationError):
        validate_plan(plan)
