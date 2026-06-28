# LoReflection

LoReflection is a closed-loop indoor semantic layout generation and editing
project. The current method is the v8 Architecture In-Context + StatePatch
pipeline.

## Current Mainline

```text
User instruction + Architecture JSON + frozen semantic registry
-> Goal State Constructor
-> Goal LoState
-> LLM Functional Prompt Compiler
-> compiled_text_prompt

Architecture JSON
-> palette-exact architecture renderer
-> architecture_condition_image

compiled_text_prompt + architecture_condition_image
-> Qwen-Image Architecture In-Context Control
-> target_full_semantic image
-> layout parser
-> layout JSON / scene JSON
-> Observed State Builder
-> Observed LoState
-> Goal-Observed Comparator / LoReview
-> Qwen3.5-VL StatePatch Editor
-> StatePatch
-> StatePatch Executor + Write-back Serializer
-> candidate layout JSON / scene JSON
-> rebuilt Observed LoState
-> Verifier / Reviewer / AcceptanceController
```

Qwen-Image is used for initial architecture-controlled semantic layout
generation. It is not the current local repair executor. Local repair is a
structured StatePatch written back to candidate layout JSON / scene JSON.

## Current Interface

- `artifacts/current_interface/statepatch.schema.json`
- `artifacts/current_interface/statepatch_editor_input_context.schema.json`
- `artifacts/current_interface/goal_lostate.schema.json`
- `artifacts/current_interface/observed_lostate.schema.json`
- `artifacts/current_interface/layout_json.schema.json`
- `artifacts/current_interface/scene_json.schema.json`
- `artifacts/current_interface/qwen_arch_incontext_metadata.schema.json`
- `outputs/current_statepatch_editor_handoff/`

Validate the current handoff:

```bash
python tools/validate_current_statepatch.py outputs/current_statepatch_editor_handoff/statepatch_sft_minimal_examples.jsonl --sft-jsonl
```

## Method Authority

Read these first:

1. `docs/CURRENT_PROJECT_STATE.md`
2. `01_论文详细文档更新_GoalObservedState_StatePatch中文版.md`
3. `02_LoState_GoalObserved_StatePatch设计文档_v8_ArchInContext中文版.md`
4. `06_Qwen-Image_Architecture_InContext_Control_方法与实验.md`
5. `docs/START_HERE.md`

## Safety Boundaries

- Do not ask the VLM to output a full Edited LoState.
- Do not ask the VLM to output executable layout JSON / scene JSON directly.
- Do not expose low-level `source_json_path` or engine uid values to the VLM.
- Keep executable writes inside the deterministic StatePatch Executor and
  Write-back Serializer.
- Keep Qwen training on the full-semantic Architecture In-Context route:
  `image=target_full_semantic`, `prompt=compiled_text_prompt`, and
  `context_image=architecture_condition_image`.

## LLM Functional Prompt Compiler

LoReflection now uses an LLM Functional Prompt Compiler as the current Qwen text-prompt path. The compiler verbalizes Goal LoState into a concise, geometry-safe Qwen-Image Architecture In-Context prompt and validates the resulting PromptPackage before it can be written to metadata.

The LLM does not generate coordinates, layout JSON, StatePatch JSON, object ids, raw source paths, or metric dimensions. It only receives a geometry-safe Goal LoState summary, semantic category registry information, active RGB palette entries, and an architecture summary limited to visible floor boundary / door / window booleans. If no LLM client is provided, prompt compilation fails with `LLM_PROMPT_CLIENT_MISSING`; there is no rule prompt fallback in the current mainline.
