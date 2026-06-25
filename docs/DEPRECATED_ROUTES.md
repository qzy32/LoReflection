# Deprecated Routes

This document records routes that are retained only as historical baselines.
They must not be presented as the current LoReflection mainline.

## C12-C14 Semantic Repair / Inpaint Baseline

Deprecated current-route concepts:

- RepairPlan
- mask_spec
- semantic_repair4
- Qwen-Image-Blockwise-ControlNet-Inpaint
- I_bad / I_target / control_mask
- blockwise_controlnet_image / blockwise_controlnet_inpaint_mask
- VLM Correction Planner
- Target LoState Constructor

These artifacts remain useful for:

- C12 sanitizer history;
- C13 small overfit provenance;
- C14 palette-contract diagnosis;
- C14.4 palette-fixed visual and training-code audit;
- baseline comparison against the new StatePatch route.

They should not be used as the active VLM handoff or the active local repair
executor.

## Current Replacement

Current local repair:

```text
Goal LoState + Observed LoState + LoReview
-> Qwen3.5-VL StatePatch Editor
-> StatePatch
-> StatePatch Executor + Write-back Serializer
-> candidate layout JSON / scene JSON
```

Current initial generation:

```text
compiled_text_prompt + architecture_condition_image
-> Qwen-Image Architecture In-Context Control
-> target_semantic_layout_image
```
