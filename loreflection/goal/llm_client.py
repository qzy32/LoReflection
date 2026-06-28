"""LLM client protocol for prompt compilation."""

from __future__ import annotations

from typing import Any, Protocol


class LLMFunctionalPromptClient(Protocol):
    def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any] | str:
        ...
