# LoReflection

LoReflection is a closed-loop indoor semantic layout generation and editing
project. The current method is the v8 Architecture In-Context + StatePatch
pipeline.

## Current Mainline

```text
User instruction + Architecture JSON + frozen semantic registry
-> Goal State Constructor
-> Goal LoState
-> Prompt Compiler
-> compiled_text_prompt

Architecture JSON
-> palette-exact architecture renderer
-> architecture_condition_image

compiled_text_prompt + architecture_condition_image
-> Qwen-Image Architecture In-Context Control
-> initial semantic layout image
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
5. `docs/MIGRATION_AUDIT_ARCH_INCONTEXT.md`
6. `docs/START_HERE.md`

The C12/C13/C14 semantic repair and inpaint experiments are historical
baselines. They remain in the repository for audit and comparison, but they are
not the current mainline.

## Safety Boundaries

- Do not train Qwen/DiffSynth inpaint as the current local repair route.
- Do not ask the VLM to output a full Edited LoState.
- Do not ask the VLM to output executable layout JSON / scene JSON directly.
- Do not expose low-level `source_json_path` or engine uid values to the VLM.
- Keep executable writes inside the deterministic StatePatch Executor and
  Write-back Serializer.
