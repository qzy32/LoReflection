# VIS-01 Evaluation and Visualization Code Guide

The evaluator is `tools/evaluate_c13_semantic_repair4_outputs.py`.

- `raw_output.png`: direct model sample.
- `snapped_output.png`: nearest frozen-palette version of raw output.
- `copyback_output.png`: final constrained output; mask outside is copied back from I_bad.
- `sanitized_output.png`: not separately emitted in C14.4.
- `diff_map.png`: red difference pixels against I_target.
- `contact_sheet.png`: evaluator quick sheet; VIS-01 creates larger annotated sheets.

The strict gate requires masked pixel accuracy >= 0.95, nonmask equality after copyback = 1.0, object_count_f1 >= 0.95, no allowed-label violations, and action_iou >= 0.85 when applicable.

VIS-01 generated annotated contact sheets and overview figures under `outputs/manual_review/vis01_c14_4_effect_report`.
