# Full Semantic Rendering Fix Summary

- Training started: false
- Full dataset regenerated: false
- Existing metadata overwritten: false
- Current mainline metadata schema: `image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs`

## Renderer Policy

palette exact; no alpha; no anti-aliasing; furniture writes to floor pixels only; void and protected architecture remain unchanged; no explicit wall RGB when wall is absent from registry.

## Review Samples

- `36c96aa6-a318-4212-aecc-22a206d7b217_room_00`: palette_exact=True, furniture_on_void=0, protected_overwrite=0, prompt_controls=True, looks_ok=True
- `36c96aa6-a318-4212-aecc-22a206d7b217_room_01`: palette_exact=True, furniture_on_void=0, protected_overwrite=0, prompt_controls=True, looks_ok=True

## Recommendation

Next step is full regeneration only if the user accepts the two sample review. Training should not start from the stale package.

## Verification

- git diff --check: pass
- pytest: 59 passed, 1 warning
- residual grep: empty
- review archive: `reports/qwen_input_prompt_review_after_renderfix/qwen_input_prompt_two_examples_after_renderfix.tar.gz`
