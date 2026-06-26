# Qwen Training Input Audit Summary

## Current Qwen Training Input

The current Qwen-Image route is Architecture In-Context Control:

`image = target_semantic_layout_image`, `prompt = compiled_text_prompt / LLM prompt`, `context_image = architecture_condition_image`.

Qwen generates furniture semantic images only. Architecture and metric scale remain sourced from raw 3D-FRONT-derived Architecture JSON.

## Metadata Field Meanings

- `image`: Qwen-Image training target. It is the target semantic furniture layout image.
- `prompt`: text prompt given to Qwen. It may be basic/template/LLM/goal-aligned depending on metadata source.
- `context_image`: architecture condition image. It should contain architecture only: room boundary, walls, doors, windows, clearance/non-placeable regions, and no furniture.
- `sample_id`: room sample id.
- `goal_lostate`: path to Goal LoState JSON for the sample.
- `prompt_package`: prompt package path. It records prompt source, LLM output, relation triplets, placement order, and related construction evidence where available.
- `verifier_refs`: validation/audit reference JSON path.

## Metadata Audits

| metadata | rows | image exists | context exists | goal exists | package exists | prompt Context_Control | coord leak | old fields |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| basic_metric_v2 | 200 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | [] |
| llm_functional | 200 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | [] |
| mixed_llm | 600 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | [] |
| goal_aligned_functional | 200 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | [] |
| goal_aligned_relation_rich | 200 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | [] |

## LLM Prompt Processing Counts

| dataset | requested | actual LLM generated | parse ok | fallback | audit status | pure LLM dataset |
|---|---:|---:|---:|---:|---|---|
| llm_functional | 200 | 200 | 1.0 | 0 | pass | None |
| goal_aligned_llm | 200 | 4 | 1.0 | 196 | pass | False |

Important: goal-aligned is contract-valid, but because fallback_count is high it should be treated as a relation-rich compiled prompt dataset, not a pure LLM prompt dataset.

## Training Status

| experiment | dataset | checkpoint | inference count | eval | status | key metrics |
|---|---|---|---:|---|---|---|
| basic_metric_v2 | True | True | 20 | True | done | agreement=0.7908599853515625, f1=0.39296374354091557, palette_after=0.0 |
| llm_functional | True | True | 20 | True | done | agreement=0.844378662109375, f1=0.45791716052151077, palette_after=0.0 |
| mixed_llm | True | False | 0 | False | running_or_incomplete | agreement=None, f1=None, palette_after=None |
| goal_aligned_llm | True | False | 0 | False | running_or_incomplete | agreement=None, f1=None, palette_after=None |

## Can Continue Training?

Do not expand to P1-1000 until the currently running mixed/goal-aligned jobs finish and their eval reports are reviewed. Basic metric_v2 and llm_functional are complete. Mixed and goal-aligned were still running at audit time.

## Next Recommendation

Review prompt examples and Goal LoState examples first. If prompt semantics are acceptable and running ablations do not regress below basic, then the next engineering step is controlled P1-1000 planning. If goal-aligned remains mostly fallback, fix the JSON-output prompt generation before calling it pure LLM data.
