from pathlib import Path


def test_no_rule_prompt_compiler_files_or_terms():
    assert not Path("loreflection/goal/prompt_compiler_rule.py").exists()
    assert not Path("runtime/prompt_builder.py").exists()
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in Path("loreflection/goal").glob("*.py"))
    assert "compile_prompt_package_rule" not in text
    assert "llm_with_rule_fallback" not in text
    assert "fallback_used" not in text
