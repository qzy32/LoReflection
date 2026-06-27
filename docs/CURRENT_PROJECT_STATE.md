# Current Project State

## Current Method Authority

The current LoReflection method is defined by the v8 Architecture In-Context
and StatePatch documents:

1. `01_论文详细文档更新_GoalObservedState_StatePatch中文版.md`
2. `02_LoState_GoalObserved_StatePatch设计文档_v8_ArchInContext中文版.md`
3. `03_Benchmark更新_GoalObserved_StatePatch中文版.md`
4. `04_实验框架更新_GoalObserved_StatePatch中文版.md`
5. `05_推动计划更新_GoalObserved_StatePatch中文版.md`
6. `06_Qwen-Image_Architecture_InContext_Control_方法与实验.md`
7. `docs/MIGRATION_AUDIT_ARCH_INCONTEXT.md`

If older C12/C13/C14 documents disagree with these files, the v8 files above
win.

## Current Mainline

```text
User instruction
+ Architecture JSON
+ frozen semantic registry
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
        -> Qwen output parser / layout parser
        -> layout JSON / scene JSON
        -> Observed State Builder
        -> Observed LoState
        -> Goal-Observed Comparator + LoRAM
        -> LoReview
        -> Qwen3.5-VL StatePatch Editor
        -> StatePatch
        -> StatePatch Executor + Write-back Serializer
        -> candidate layout JSON / scene JSON
        -> Rebuild Observed LoState
        -> Programmatic Verifier + VLM Reviewer + AcceptanceController
```

## Initial Generation

The current initial generation module is Qwen-Image Architecture In-Context
Control:

```text
compiled_text_prompt + architecture_condition_image
-> target_semantic_layout_image
```

The DiffSynth training metadata for this route is:

```csv
image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs
```

Meanings:

- `image` = `target_semantic_layout_image`
- `prompt` = `compiled_text_prompt`
- `context_image` = `architecture_condition_image`

Qwen does not perform local repair in the current mainline.

## Local Repair / Editing

Local repair is performed by a Qwen3.5-VL StatePatch Editor. The editor outputs
only `StatePatch` JSON. The executor resolves the patch against Observed LoState
and writes candidate layout JSON / scene JSON. It does not write a LoState JSON
as the executable artifact.

Current StatePatch actions:

- ADD
- REMOVE
- TRANSLATE
- ROTATE
- SCALE
- REPLACE

Current interface files:

- `artifacts/current_interface/statepatch.schema.json`
- `artifacts/current_interface/statepatch_editor_input_context.schema.json`
- `artifacts/current_interface/goal_lostate.schema.json`
- `artifacts/current_interface/observed_lostate.schema.json`
- `artifacts/current_interface/layout_json.schema.json`
- `artifacts/current_interface/scene_json.schema.json`
- `artifacts/current_interface/qwen_arch_incontext_metadata.schema.json`
- `outputs/current_statepatch_editor_handoff/`

## Historical Baseline

The C12/C13/C14 semantic repair work is retained as historical evidence and a
baseline. It is not the current mainline. This baseline includes the legacy
RepairPlan planner handoff, mask planning, semantic repair routing,
Qwen/DiffSynth blockwise inpaint training, `I_bad`, `I_target`, and
`control_mask` artifacts.

Do not delete those files without a separate archive decision; they document the
C14.4 palette-fixed diagnostic result and remain useful for comparison.

## Current P0 Status

The repository now contains a bounded Qwen Architecture In-Context P0 builder,
audits, previews, and tests. A local 60-sample deterministic procedural package
passes the `image,prompt,context_image` contract:

- condition images are architecture-only;
- target images are full semantic;
- frozen-palette and prompt-leakage audits pass;
- scene-grouped splits have no cross-split scene leakage.

The generated package is contract-validation data, not real 3D-FRONT benchmark
data and not model-quality evidence.

## Current Next Step

Feed 50-200 real scene-package architecture/layout pairs into the P0 builder,
rerun the same gates, manually inspect the preview, and only then run a bounded
Architecture In-Context pipeline sanity training.

## StatePatch Strict SFT Protocol

For VLM SFT/inference, StatePatch uses the strict subset documented in `outputs/current_statepatch_editor_handoff/STATEPATCH_SFT_STRICT_PROTOCOL.md`. The JSON schema is intentionally wider, but training should not mix relative and absolute update modes. In the strict subset, TRANSLATE uses relative `delta_m`, ROTATE uses relative `delta_deg`, SCALE uses relative `scale_xy`, ADD uses placement hints, and bbox/full executable JSON outputs are forbidden.
