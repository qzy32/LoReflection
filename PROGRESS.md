# Progress

## Current Status

LoReflection has migrated its documented current route to the v8 Architecture
In-Context + StatePatch method.

Current mainline:

```text
Goal State Constructor
-> Goal LoState
-> Prompt Compiler
-> compiled_text_prompt
+ architecture_condition_image
-> Qwen-Image Architecture In-Context Control
-> target_semantic_layout_image
-> layout JSON / scene JSON
-> Observed LoState
-> LoReview
-> Qwen3.5-VL StatePatch Editor
-> StatePatch
-> StatePatch Executor + Write-back Serializer
-> candidate layout JSON / scene JSON
-> verification and acceptance
```

## Completed

- C14.4 palette-fixed semantic repair training completed and is retained as a
  historical diagnostic baseline.
- `docs/MIGRATION_AUDIT_ARCH_INCONTEXT.md` identified the old route residuals.
- Current interface schemas for StatePatch and Qwen Architecture In-Context
  metadata have been added.
- A current StatePatch editor handoff package has been added.
- Validators and tests have been added for StatePatch, metadata, prompt leakage,
  and architecture-condition furniture-color leakage.
- A 60-sample deterministic procedural P0 contract package has been generated
  locally under `data/loreflection_qwen_arch_control/`. Metadata, palette,
  prompt, split, condition/target separation, and preview audits pass.
- The P0 package validates the software and data contract only. It is not a
  replacement for a real 3D-FRONT/3D-FUTURE scene package.

## Historical Baseline

The C12/C13/C14 work remains useful as provenance and comparison. It includes
legacy RepairPlan planning, mask planning, semantic repair routing, and
Qwen/DiffSynth blockwise inpaint experiments. It is not the current executable
mainline.

## Next Step

Connect the P0 builder to real scene-package outputs:

1. supply 50-200 real scene-grouped architecture/layout pairs;
2. rerun the same metadata, palette, prompt, split, and visual audits;
3. manually inspect architecture-condition diversity and target fidelity;
4. then run a bounded P0 pipeline sanity training, without treating procedural
   samples as model-quality evidence.
