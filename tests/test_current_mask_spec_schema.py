import copy
import json
from pathlib import Path

import pytest

from tools.validate_current_repairplan import ValidationError, validate_plan


def _plan(action: str):
    path = Path("outputs/current_vlm_planner_handoff/planner_sft_minimal_examples.jsonl")
    for line in path.read_text(encoding="utf-8").splitlines():
        plan = json.loads(json.loads(line)["conversations"][-1]["value"])
        if plan["action_type"] == action:
            return plan
    raise AssertionError(action)


def test_bbox_component_requires_bbox_px():
    plan = copy.deepcopy(_plan("ADD"))
    component = plan["mask_spec"]["components"][0]
    component["geometry"] = {}
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_bbox_component_requires_positive_extent():
    plan = copy.deepcopy(_plan("ADD"))
    component = plan["mask_spec"]["components"][0]
    component["geometry"]["bbox_px"] = [10, 10, 10, 20]
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_bbox_component_must_stay_inside_image():
    plan = copy.deepcopy(_plan("ADD"))
    component = plan["mask_spec"]["components"][0]
    component["geometry"]["bbox_px"] = [-1, 10, 20, 30]
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_allowed_labels_cannot_be_empty():
    plan = copy.deepcopy(_plan("ADD"))
    plan["mask_spec"]["components"][0]["allowed_labels"] = []
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_polygon_requires_at_least_three_points():
    plan = copy.deepcopy(_plan("ADD"))
    component = plan["mask_spec"]["components"][0]
    component["geometry_type"] = "polygon"
    component["geometry"] = {"polygon_px": [[0, 0], [10, 10]]}
    with pytest.raises(ValidationError):
        validate_plan(plan)


def test_instance_ref_requires_instance_ref_geometry():
    plan = copy.deepcopy(_plan("ADD"))
    component = plan["mask_spec"]["components"][0]
    component["geometry_type"] = "instance_ref"
    component["geometry"] = {}
    with pytest.raises(ValidationError):
        validate_plan(plan)
