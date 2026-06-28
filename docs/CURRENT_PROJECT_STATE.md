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
If older experiment notes disagree with these files, the v8 files above win.

## Current Mainline

```text
User instruction
+ Architecture JSON
+ frozen semantic registry
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
-> target_full_semantic
```

The DiffSynth training metadata for this route is:

```csv
image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs
```

Meanings:

- `image` = `target_full_semantic`
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

## Current Qwen Data Status

The current Qwen training data route is `full_semantic_compiled_main`:

- input prompt: LLM Functional PromptPackage `compiled_text_prompt`;
- input image: palette-exact `architecture_condition_image`;
- supervised image: palette-exact `target_full_semantic`;
- metadata columns: `image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs`.

## Current Next Step

Monitor Qwen LoRA training, then run inference, quantization, and evaluation on
the produced checkpoints.

## StatePatch Strict SFT Protocol

For VLM SFT/inference, StatePatch uses the strict subset documented in `outputs/current_statepatch_editor_handoff/STATEPATCH_SFT_STRICT_PROTOCOL.md`. The JSON schema is intentionally wider, but training should not mix relative and absolute update modes. In the strict subset, TRANSLATE uses relative `delta_m`, ROTATE uses relative `delta_deg`, SCALE uses relative `scale_xy`, ADD uses placement hints, and bbox/full executable JSON outputs are forbidden.

## LLM Functional Prompt Compiler

LoReflection now uses an LLM Functional Prompt Compiler as the current Qwen text-prompt path. The compiler verbalizes Goal LoState into a concise, geometry-safe Qwen-Image Architecture In-Context prompt and validates the resulting PromptPackage before it can be written to metadata.

The LLM does not generate coordinates, layout JSON, StatePatch JSON, object ids, raw source paths, or metric dimensions. It only receives a geometry-safe Goal LoState summary, semantic category registry information, active RGB palette entries, and an architecture summary limited to visible floor boundary / door / window booleans. If no LLM client is provided, prompt compilation fails with `LLM_PROMPT_CLIENT_MISSING`; there is no rule prompt fallback in the current mainline.
