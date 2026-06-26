from loreflection.qwen_arch_control.prompt_labels.template_prompt_generator import generate_prompt_variants
from tools.audit_prompt_geometry_leakage import find_leaks


def test_prompt_variants_cover_slots_and_have_no_geometry():
    facts = {"room_type": "bedroom", "furniture_counts": {"double_bed": 1, "nightstand": 2}, "primary_anchor": "double_bed", "global_constraints": []}
    variants = generate_prompt_variants(facts)
    assert set(variants) == {"template_minimal", "template_functional", "template_user_like"}
    for prompt in variants.values():
        assert prompt.startswith("Context_Control.")
        assert "double bed" in prompt and "nightstand" in prompt
        assert not find_leaks(prompt)
