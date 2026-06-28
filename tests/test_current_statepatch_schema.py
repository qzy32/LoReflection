import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.validate_current_statepatch import ValidationError, validate_statepatch


SCHEMA = json.loads(Path("artifacts/current_interface/statepatch.schema.json").read_text(encoding="utf-8"))


def _valid_patch():
    return {
        "schema_version": "statepatch-v1.2",
        "patch_id": "patch_0001",
        "patch_target_space": "observed_lostate_view",
        "execution_target_space": "layout_json",
        "source_observed_state_id": "obs_state_round_0",
        "action_type": "TRANSLATE",
        "target": {"target_ref": "obs:bed_001", "expected_category": "bed"},
        "state_field_updates": {"center_m": {"update_mode": "relative_delta", "delta_m": [0.6, 0.0]}},
        "reason": "bed overlaps door clearance",
        "constraints_to_satisfy": ["door_clearance_free", "inside_room", "no_collision"],
        "protected_refs": ["obs:wardrobe_001"],
    }


def test_valid_statepatch_schema_and_validator():
    patch = _valid_patch()
    Draft202012Validator(SCHEMA).validate(patch)
    validate_statepatch(patch)


def test_statepatch_rejects_extra_fields_and_raw_paths():
    patch = _valid_patch()
    patch["unexpected_field"] = {}
    with pytest.raises(Exception):
        Draft202012Validator(SCHEMA).validate(patch)

    patch = _valid_patch()
    patch["reason"] = "contains source_json_path"
    with pytest.raises(ValidationError):
        validate_statepatch(patch)


def test_non_remove_requires_state_field_updates():
    patch = _valid_patch()
    del patch["state_field_updates"]
    with pytest.raises(Exception):
        Draft202012Validator(SCHEMA).validate(patch)


def test_remove_may_omit_state_field_updates():
    patch = copy.deepcopy(_valid_patch())
    patch["action_type"] = "REMOVE"
    patch["target"] = {"target_ref": "obs:chair_002", "expected_category": "chair"}
    del patch["state_field_updates"]
    Draft202012Validator(SCHEMA).validate(patch)
    validate_statepatch(patch)
