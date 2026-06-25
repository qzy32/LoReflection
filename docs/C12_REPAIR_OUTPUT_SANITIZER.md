# C12 Repair Output Sanitizer

## Scope

C12 validates semantic_repair4 data only: ADD, REMOVE, TRANSLATE, and REPLACE. ROTATE and SCALE are parametric_update actions and are not included in the Qwen/DiffSynth sanitizer input.

## Current Result

After replacing no-op rows and rerunning the sanitizer, C12 result is `C12_PASS`.

- rows: 12
- actions: {'ADD': 3, 'REMOVE': 3, 'TRANSLATE': 3, 'REPLACE': 3}
- failed samples: 0
- policy threshold: min_component_area_px = 16
- semantic input contains ROTATE/SCALE: False

## Outputs

- `reports/c12_sanitizer_eval.json`
- `reports/c12_sanitizer_eval.csv`
- `reports/c12_sanitizer_policy_sweep.json`
- `reports/c12_sanitizer_policy_sweep.csv`
- `outputs/manual_review/c12_sanitizer/`

## Gate

C12_PASS allowed the C13 semantic_repair4 dataset package and small overfit runs to proceed.
