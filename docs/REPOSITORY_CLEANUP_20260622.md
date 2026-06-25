# Repository Cleanup 2026-06-22

## Result

The cleanup used the current interface, handoff, tests, and C12-C14 documentation
as the authority. Ambiguous historical material was kept or archived instead of
being permanently deleted.

Current protocol after cleanup:

- Planner actions: ADD, REMOVE, TRANSLATE, ROTATE, SCALE, REPLACE
- semantic_repair4: ADD, REMOVE, TRANSLATE, REPLACE
- parametric_update: ROTATE, SCALE

## Deleted

Only regenerable caches and one empty generated directory were deleted:

- `.pytest_cache/`
- `scripts/__pycache__/`
- `tests/__pycache__/`
- `tools/__pycache__/`
- `outputs/closed_loop_smoke/`

## Archived

Twenty-eight zero-reference historical objects were moved under
`_archive/deprecated_20260622/`. They include old candidate registry configs,
duplicate review archives, pre-C11/C12 visual packages, old val50 and C8G/R8
outputs, stale structure snapshots, a pre-replacement C12 manifest, and temporary
C14.4 daemon logs. The archive contains 565 files and is about 9.24 MiB.

The structure guide and CSV/JSON indexes now point to the archived locations.

## Kept Despite Old Names

- `artifacts/semantic_registry_v1/`: migration tests and audit reports use its
  deprecated sentinel.
- `schemas/*_v1.schema.json`: legacy validation tools still reference them.
- `configs/palette_v2_qwenimage_candidate.json`: the frozen palette and tests
  still reference this palette identity.
- `configs/semantic_target_registry_v2_candidate.yaml`: a current test imports it.
- C11-C14 reports, configs, scripts, and selected manual-review folders: current
  documentation uses them as the reproducibility and audit chain.
- `outputs/manual_review/current_repair_protocol_review_package/`: its archive is
  explicitly referenced by the C11.11 cleanup report.

## Manual Review

Do not delete the following without a separate migration decision:

- legacy v1 schemas plus `tools/validate_all.py` and
  `tools/validate_unified_toy_package.py`
- `examples/toy_samples/`, `data_pipeline/`, `runtime/run_closed_loop.py`, and
  `vlm/infer_planner.py`, which still contain old action vocabulary
- root historical design Markdown/PDF files
- large historical provenance reports such as
  `reports/u1_unified_freeze_training_summary.json`
- server command mirrors such as `scripts/fix_c11_10_dryrun_remote.py`

## Protocol Conflict Fixed

The current schema already used execution mode `parametric_update`, while the
current manifest, handoff action protocol, validator constant, and one test still
used the route label `parametric_repair2`. These current-scope remnants were
normalized to `parametric_update`, and the current handoff ZIP was rebuilt.

## Validation

- RepairPlan validator: PASS
- Full pytest: 45 passed
- Current-scope deprecated execution names: no remaining hits
- Cleanup-caused broken references: none

Two dataset paths referenced by current docs are server-side artifacts and are
not expected in the local checkout. The docs now say this explicitly.

Machine-readable details: `reports/repository_cleanup_20260622.json`.
