from loreflection.goal.prompt_compiler import compile_prompt_package
from tools.audit_prompt_geometry_leakage import audit_texts


def test_prompt_compiler_does_not_leak_geometry():
    goal = {
        "schema_version": "goal-lostate-v2",
        "metadata": {"task_id": "case_001"},
        "room_type": "bedroom",
        "furniture_slots": [
            {"slot_id": "goal:bed", "category": "double_bed", "required": True, "count": 1, "role": "primary_anchor"},
            {"slot_id": "goal:desk", "category": "desk", "required": True, "count": 1},
        ],
        "goal_constraints": [
            {
                "constraint_id": "gc_safe",
                "constraint_kind": "region",
                "domain": "object_region",
                "necessity": "required",
                "prompt_hint": "Keep the bed away from door clearance.",
                "verification": {"type": "opening_clearance"},
            },
            {
                "constraint_id": "gc_leaky",
                "constraint_kind": "region",
                "domain": "object_region",
                "necessity": "required",
                "prompt_hint": "Do not expose center_m or bbox in prompt.",
            },
        ],
        "verification_profile": {},
        "prompt_compilation_policy": {},
    }
    package = compile_prompt_package(goal)
    prompt = package["compiled_text_prompt"]
    assert prompt.startswith("Context_Control.")
    assert "center_m" not in prompt
    assert "bbox" not in prompt
    assert audit_texts([prompt])["status"] == "pass"



def test_rule_prompt_includes_palette_rgb_entries():
    package = compile_prompt_package({
        "room_type": "bedroom",
        "furniture_slots": [{"slot_id": "goal:bed", "category": "double_bed", "count": 1, "required": True}],
        "goal_constraints": [],
        "required_counts": {"double_bed": 1},
    }, registry=type("R", (), {"palette": {"double_bed": [72, 224, 199]}})())
    assert "Palette_Control." in package["compiled_text_prompt"]
    assert "double_bed=(72,224,199)" in package["compiled_text_prompt"]
