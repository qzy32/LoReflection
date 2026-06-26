from loreflection.qwen_arch_control.prompt_labels.palette_contract import (
    build_palette_control_prompt,
    get_active_palette_entries,
    validate_active_palette_entries,
)


def test_active_palette_entries_cover_required_categories():
    c2rgb = {"desk": [1, 2, 3], "double_bed": [4, 5, 6]}
    active = get_active_palette_entries({"desk": 1, "chair": 0}, c2rgb)
    assert active == {"desk": [1, 2, 3]}
    assert validate_active_palette_entries(["desk"], c2rgb)["valid"]


def test_palette_control_prompt_names_active_categories_without_rgb_by_default():
    prompt = build_palette_control_prompt(["desk", "double_bed"])
    assert "Palette_Control." in prompt
    assert "desk" in prompt
    assert "double_bed" in prompt
    assert "[1" not in prompt
