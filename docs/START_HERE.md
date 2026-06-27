# Start Here

This is the short onboarding map for the current LoReflection method.

## Current Protocol

LoReflection is now organized around:

- Qwen-Image Architecture In-Context Control for initial semantic layout
  generation.
- Qwen3.5-VL StatePatch Editor for local repair decisions.
- StatePatch Executor + Write-back Serializer for candidate layout JSON /
  scene JSON writes.

Qwen does not do local repair in the current mainline.

## Read These First

1. `docs/CURRENT_PROJECT_STATE.md` - source of truth for the current route.
2. `01_论文详细文档更新_GoalObservedState_StatePatch中文版.md` - method boundary.
3. `02_LoState_GoalObserved_StatePatch设计文档_v8_ArchInContext中文版.md` - Goal/Observed/StatePatch schema details.
4. `06_Qwen-Image_Architecture_InContext_Control_方法与实验.md` - Qwen initial generation data format.
5. `docs/MIGRATION_AUDIT_ARCH_INCONTEXT.md` - old-route audit and migration notes.
6. `README.md` and `PROGRESS.md`.

## Current Interface

1. `artifacts/current_interface/statepatch.schema.json`
2. `artifacts/current_interface/statepatch_editor_input_context.schema.json`
3. `artifacts/current_interface/qwen_arch_incontext_metadata.schema.json`
4. `tools/validate_current_statepatch.py`
5. `tools/validate_arch_incontext_training_metadata.py`
6. `tools/audit_prompt_geometry_leakage.py`
7. `tools/audit_architecture_condition_no_furniture.py`
8. `outputs/current_statepatch_editor_handoff/`

## If You Are A VLM Teammate

Start with:

1. `outputs/current_statepatch_editor_handoff/README_STATEPATCH_EDITOR_HANDOFF.md`
2. `outputs/current_statepatch_editor_handoff/INPUT_CONTEXT_SPEC.md`
3. `outputs/current_statepatch_editor_handoff/STATEPATCH_OUTPUT_SPEC.md`
4. `outputs/current_statepatch_editor_handoff/statepatch_sft_minimal_examples.jsonl`
5. `tools/validate_current_statepatch.py`

## If You Are Building Qwen Initial Generation Data

Use metadata rows with:

```csv
image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs
```

Where:

- `image` is the target semantic layout image.
- `prompt` is the compiled text prompt.
- `context_image` is the architecture condition image.

## Historical Baseline

The old RepairPlan planner handoff, mask planning, semantic repair routing, and
Qwen/DiffSynth blockwise inpaint artifacts are retained only as the C12-C14
historical baseline. See `docs/DEPRECATED_ROUTES.md`.

## Do Not Do This Without A New Protocol Decision

- Do not turn the historical inpaint route back into the current repair route.
- Do not change taxonomy, palette, or semantic registry.
- Do not ask the VLM to output a full Edited LoState or executable scene file.
- Do not print server credentials or local environment files.

## StatePatch Strict SFT Protocol

VLM teammates should read `outputs/current_statepatch_editor_handoff/STATEPATCH_SFT_STRICT_PROTOCOL.md` before StatePatch SFT or inference work.

For StatePatch SFT, follow the strict subset protocol instead of using every mode allowed by the wider JSON schema.
