"""Public LLM-only Prompt Compiler facade."""

from __future__ import annotations

from typing import Any

from .llm_functional_prompt_compiler import build_architecture_summary, compile_prompt_package as compile_llm_functional_prompt_package


def compile_prompt_package(
    goal_lostate: dict[str, Any],
    architecture_summary: dict[str, Any] | None = None,
    registry: Any | None = None,
    llm_client: Any | None = None,
) -> dict[str, Any]:
    """Compile Goal LoState into a validated LLM Functional PromptPackage.

    This facade intentionally has no rule/template path. If ``llm_client`` is
    missing or the LLM output fails validation, compilation fails.
    """
    return compile_llm_functional_prompt_package(
        goal_lostate,
        architecture_summary=architecture_summary,
        registry=registry,
        llm_client=llm_client,
    )
