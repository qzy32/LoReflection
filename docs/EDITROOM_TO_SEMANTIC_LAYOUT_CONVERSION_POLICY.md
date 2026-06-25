# EditRoom to SemLayoutDiff-Style Semantic Layout Conversion Policy

The current bridge name is EditRoom official-data conversion bridge.

The bridge renders real EditRoom before/after Room pickle pairs into LoReflection fixed-palette 512x512 top-down semantic PNGs. It does not reuse EditRoom visualization renders.

Current semantic_repair4 conversion:

- ADD: before lacks target object, after contains target object; mask = after target footprint + dilation.
- REMOVE: before contains source object, after removes it; mask = before source footprint + dilation.
- TRANSLATE: same object moves; mask = old footprint union new footprint, disconnected mask allowed.
- REPLACE: before source category, after target category; mask = source footprint union target footprint.

Current parametric_update conversion:

- ROTATE: valid Planner action, excluded from Qwen/DiffSynth semantic repair metadata.
- SCALE: valid Planner action, excluded from Qwen/DiffSynth semantic repair metadata.

C11.10 generated compatibility exploration rows for ROTATE, but current C12 semantic_repair4 metadata must exclude ROTATE and SCALE. Same-class touching objects remain a sanitizer/evaluator concern.
