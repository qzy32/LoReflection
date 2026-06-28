# LLM Functional Prompt Compiler Cleanup

- Training started: no
- Full data regeneration: no
- metadata.csv overwritten: no
- Current prompt compiler: `llm_functional` only
- Rule-based compiler: removed from current mainline
- Rule fallback: removed; missing client raises `LLM_PROMPT_CLIENT_MISSING`
- Active RGB palette entries: compiled into `compiled_text_prompt` by the compiler

## Review Samples

- `36c96aa6-a318-4212-aecc-22a206d7b217_room_00`: `reports/llm_functional_prompt_compiler_cleanup/review_samples/36c96aa6-a318-4212-aecc-22a206d7b217_room_00/review.md`; validation `pass`; RGB entries `True`
- `faf62fbc-739a-40da-aac3-12b6807ee7e3_room_02`: `reports/llm_functional_prompt_compiler_cleanup/review_samples/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_02/review.md`; validation `pass`; RGB entries `True`
- `faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05`: `reports/llm_functional_prompt_compiler_cleanup/review_samples/faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05/review.md`; validation `pass`; RGB entries `True`

## Verification

- `git diff --check`: pass
- Pytest: `75 passed, 1 warning`
- Focused current prompt compiler grep: pass / empty
- Broad residual grep note: the broad command still matches legacy prompt-label variant tests/docs and renderer `fallback_used` for footprint fallback, not the current prompt compiler.
- Training started: no
- Full data regeneration: no
- metadata.csv overwritten: no
