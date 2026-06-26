import json

from loreflection.qwen_arch_control.prompt_labels.prompt_compiler_v2 import compile_prompt_package_v2


def test_prompt_compiler_v2_appends_architecture_and_palette_control(tmp_path):
    palette = tmp_path / "c2rgb.json"
    palette.write_text(json.dumps({"desk": [1, 2, 3], "double_bed": [4, 5, 6]}), encoding="utf-8")
    package = compile_prompt_package_v2(
        user_intent_prompt="Context_Control. Create a study with one desk.",
        goal_lostate={"required_counts": {"desk": 1}},
        prompt_package={"schema_version": "prompt-package-test"},
        c2rgb_path=palette,
    )
    assert package["compiled_prompt"].startswith("Context_Control.")
    assert "Architecture_Control." in package["compiled_prompt"]
    assert "Palette_Control." in package["compiled_prompt"]
    assert package["active_palette_entries"] == {"desk": [1, 2, 3]}
