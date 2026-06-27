"""Prompt Compiler facade for Qwen-Image Architecture In-Context Control."""

from __future__ import annotations

from typing import Any, Literal

from .prompt_compiler_llm import build_architecture_summary, compile_prompt_package_llm
from .prompt_compiler_rule import compile_prompt_package_rule

PromptCompilerMode = Literal["rule", "llm", "llm_functional", "llm_with_rule_fallback"]


def compile_prompt_package(goal_lostate: dict[str, Any], architecture_summary: dict[str, Any] | None = None, registry: Any | None = None, llm_client: Any | None = None, mode: PromptCompilerMode = "llm_with_rule_fallback") -> dict[str, Any]:
    """Compile a Goal LoState into a geometry-safe Qwen prompt package.

    The default is LLM functional verbalization with deterministic rule fallback.
    LLM modes only verbalize Goal LoState and architecture visibility summaries;
    they never generate coordinates, layout JSON, or scene JSON.
    """

    if mode == "rule":
        return compile_prompt_package_rule(goal_lostate, architecture_summary, registry)
    if mode in {"llm", "llm_functional"}:
        return compile_prompt_package_llm(goal_lostate, architecture_summary, registry, llm_client, fallback=False)
    if mode == "llm_with_rule_fallback":
        return compile_prompt_package_llm(goal_lostate, architecture_summary, registry, llm_client, fallback=True)
    raise ValueError(f"Unsupported prompt compiler mode: {mode}")
