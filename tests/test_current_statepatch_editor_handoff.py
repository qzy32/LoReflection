import json
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.validate_current_statepatch import extract_patches, validate_statepatch


def test_current_statepatch_handoff_files_exist():
    root = Path("outputs/current_statepatch_editor_handoff")
    for name in [
        "README_STATEPATCH_EDITOR_HANDOFF.md",
        "STATEPATCH_OUTPUT_SPEC.md",
        "INPUT_CONTEXT_SPEC.md",
        "statepatch_sft_minimal_examples.jsonl",
        "schemas/statepatch.schema.json",
        "schemas/statepatch_editor_input_context.schema.json",
    ]:
        assert (root / name).exists()


def test_statepatch_handoff_examples_validate():
    path = Path("outputs/current_statepatch_editor_handoff/statepatch_sft_minimal_examples.jsonl")
    patches = extract_patches(path, sft_jsonl=True)
    assert patches
    for patch in patches:
        validate_statepatch(patch)


def test_statepatch_editor_input_context_schema_accepts_minimal_context():
    schema = json.loads(Path("artifacts/current_interface/statepatch_editor_input_context.schema.json").read_text(encoding="utf-8"))
    context = {
        "schema_version": "statepatch-editor-input-context-v1",
        "task_tag": "[STATEPATCH_EDITING]",
        "goal_lostate": {"schema_version": "goal-lostate-v2"},
        "observed_lostate": {"schema_version": "observed-lostate-v2"},
        "loreview": {"issues": [{"issue_id": "issue_1"}]},
        "architecture_ref": {"architecture_id": "arch_001"},
        "allowed_actions": ["ADD", "REMOVE", "TRANSLATE", "ROTATE", "SCALE", "REPLACE"],
        "statepatch_output_spec": {"schema": "statepatch-v1.2"},
        "verification_profile": {"hard_checks": ["inside_room"]},
    }
    Draft202012Validator(schema).validate(context)

