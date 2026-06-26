from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SYSTEM = "You generate coordinate-free indoor layout instructions from structured facts. Do not mention coordinates, sizes, pixels, meters, source paths, or hidden IDs."


def make_request(sample_id: str, scene_facts: dict[str, Any], rich_goal: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "system": SYSTEM,
        "user": {"scene_facts": scene_facts, "goal_lostate_rich_without_geometry": rich_goal},
        "required_output_schema": {
            "prompt_llm_short": "string",
            "prompt_llm_functional": "string",
            "prompt_llm_user_like": "string",
        },
    }


def write_requests(path: Path, requests: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
