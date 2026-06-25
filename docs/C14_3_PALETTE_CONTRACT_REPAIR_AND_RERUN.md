# C14.3 Palette Contract Repair And Clean Medium Re-run

Current protocol is unchanged: semantic_repair4 contains ADD, REMOVE, TRANSLATE, REPLACE; ROTATE and SCALE remain parametric_update only.

## Palette Audit

Frozen palette: `artifacts/semantic_registry_v2/palette_frozen.json`.

Palette audit result: `PALETTE_MISMATCH_REPAIRABLE_BY_LABEL`.

Repair strategy: Strategy B, old SemLayoutDiff native RGB -> semantic label -> frozen RGB. No nearest-RGB blind conversion was used.

## Palette-Fixed Dataset

New dataset: `/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_medium_dataset_v2_palette_fixed`.

Rows: 80 total, 20 per action.

Data gate: `C14_3_DATA_PASS`.

Evaluator self-test: `EVAL_OK`.

The first palette-fixed self-test exposed a second, narrower policy issue:
several white-mask target regions legitimately contained additional frozen
semantic ids such as fixed architectural labels. The v2 allowed-label repair
augmented each component with every frozen semantic id present in `I_target`
inside the full white mask. After that repair, the full 80-row self-test passed:

- `I_target`: 80 / 80 edit_success
- oracle copyback: 80 / 80 edit_success
- `I_bad`: 0 / 80 edit_success
- random fixed-palette image: 0 / 80 edit_success

DiffSynth loader dry-run: `LOADER_PASS`.

## C14.1 Invalidation

C14.1 checkpoints are retained for audit but invalidated as model-quality evidence because they were trained/evaluated under a palette-contract mismatch.

## Next Step

This step is complete. C14.4 subsequently selected GPU0 and completed the
palette-fixed clean REMOVE, REPLACE, TRANSLATE, ADD, and MIXED_80 runs.
All four single actions produced nonzero action-specific metrics. See
`docs/C14_4_PALETTE_FIXED_CLEAN_TRAINING_RESULT.md`.
