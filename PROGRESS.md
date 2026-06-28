# Progress

## Current Status

LoReflection has migrated its documented current route to the v8 Architecture
In-Context + StatePatch method.

Current mainline:

```text
Goal State Constructor
-> Goal LoState
-> LLM Functional Prompt Compiler
-> compiled_text_prompt
+ architecture_condition_image
-> Qwen-Image Architecture In-Context Control
-> target_full_semantic
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

- Current interface schemas for StatePatch and Qwen Architecture In-Context
  metadata have been added.
- A current StatePatch editor handoff package has been added.
- The Qwen route has been consolidated to `full_semantic_compiled_main`.
- The Qwen prompt path is LLM-only: Goal LoState plus a geometry-safe
  architecture summary is compiled into a validated PromptPackage.
- Full-semantic Qwen data is generated with `image,prompt,context_image` only.
- Retired Qwen repair, prompt-ablation, and auxiliary target artifacts have
  been removed from the tracked mainline.

## Next Step

Continue training and evaluation on the full-semantic Architecture In-Context
data package:

1. monitor the active Qwen LoRA training run;
2. run inference, quantization, and evaluation once checkpoints are available;
3. only promote checkpoints that pass palette, architecture-preservation, and
   furniture reconstruction gates.

## LLM Functional Prompt Compiler

LoReflection now uses an LLM Functional Prompt Compiler as the current Qwen text-prompt path. The compiler verbalizes Goal LoState into a concise, geometry-safe Qwen-Image Architecture In-Context prompt and validates the resulting PromptPackage before it can be written to metadata.

The LLM does not generate coordinates, layout JSON, StatePatch JSON, object ids, raw source paths, or metric dimensions. It only receives a geometry-safe Goal LoState summary, semantic category registry information, active RGB palette entries, and an architecture summary limited to visible floor boundary / door / window booleans. If no LLM client is provided, prompt compilation fails with `LLM_PROMPT_CLIENT_MISSING`; there is no rule prompt fallback in the current mainline.
