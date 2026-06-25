# C12 Sanitizer Current Plan

C12 uses real converted EditRoom semantic samples from C11.10.

semantic_repair4 actions entering Qwen/DiffSynth sanitizer path:

- ADD
- REMOVE
- TRANSLATE
- REPLACE

parametric_update actions outside Qwen semantic repair:

- ROTATE
- SCALE

C12 must not include ROTATE or SCALE in DiffSynth metadata. C11.10 generated ROTATE compatibility exploration rows, but those rows are excluded from current semantic_repair4 training by the final protocol. SCALE remains parametric_update.
