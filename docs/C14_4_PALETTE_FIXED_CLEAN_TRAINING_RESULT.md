# C14.4 Palette-Fixed Clean Training Result

Source of truth: `docs/CURRENT_PROJECT_STATE.md`.

The protocol was unchanged:

- Planner-facing actions: ADD, REMOVE, TRANSLATE, ROTATE, SCALE, REPLACE
- semantic_repair4: ADD, REMOVE, TRANSLATE, REPLACE
- parametric_update: ROTATE, SCALE

ROTATE and SCALE did not enter Qwen/DiffSynth training or metadata.

## Pretrain Gate

- RepairPlan validator: PASS
- current protocol tests: PASS, 15 passed
- palette-fixed data gate: `C14_3_DATA_PASS`
- evaluator self-test: `EVAL_OK`
- DiffSynth loader dry-run: `LOADER_PASS`

## GPU Selection

The daemon selected GPU0, an NVIDIA A800-SXM4-80GB, with 81219 MiB free
memory and 0% utilization. The original wait was approximately 105 minutes.
The corrected fixed-step run started immediately once GPU0 was available.

No other users' processes were killed. Peak training memory was approximately
60.7 GB allocated and 61.6 GB reserved.

## Orchestration Correction

The first C14.4 wrapper combined `DATASET_REPEAT=15` and `NUM_EPOCHS=15`,
which continued beyond the requested 300 steps. Only this project's own
daemon/training processes were stopped. Those extra checkpoints are retained
for audit and are not used for the C14.4 conclusion.

The corrected run used the new `c14_4_fixedsteps` tag:

- single actions: `DATASET_REPEAT=1`, `NUM_EPOCHS=15`, exactly 300 steps
- MIXED_80: epoch-based run reached step 300 and ended at step 320
- all C14.4 mixed evaluation and conclusions use the step-300 checkpoint

After the clean run, the wait-and-run script was tightened so future formal
runs save only the smoke checkpoint at step 20 and the main checkpoint at step
300. Existing overrun checkpoints were not deleted automatically because model
weight deletion is outside the C14.4 safety envelope unless explicitly scoped.

## First Valid Results

| Run | Steps used | Last loss | Edit success | Masked accuracy | Action IoU | Snapped palette | Nonmask equality | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| REMOVE | 300 | 0.000496 | 0.60 | 0.914 | 0.914 | 1.0 | 1.0 | CLEAN_ACTION_PARTIAL |
| REPLACE | 300 | 0.001729 | 0.00 | 0.478 | 0.611 | 1.0 | 1.0 | CLEAN_ACTION_PARTIAL |
| TRANSLATE | 300 | 0.002111 | 0.00 | 0.792 | 0.683 | 1.0 | 1.0 | CLEAN_ACTION_PARTIAL |
| ADD | 300 | 0.002530 | 0.00 | 0.637 | 0.806 | 1.0 | 1.0 | CLEAN_ACTION_PARTIAL |
| MIXED_80 | 300 | 0.002473 | 0.00 | 0.502 | 0.800 | 1.0 | 1.0 | CLEAN_ACTION_PARTIAL |

This is the first valid C14 palette-fixed model-quality signal. All four
single-action runs produced nonzero action-specific metrics, so MIXED_80 was
allowed and completed. REMOVE is the only sampled run with nonzero strict
edit success.

Evaluation sampled five rows per action at step 100 and step 300. The current
`infer-action` wrapper requires a LoRA path, so a separate base/step0 run was
not emitted. The visual output stages are `raw_output.png`,
`snapped_output.png`, and final constrained `copyback_output.png`; this
evaluator does not emit a separate file named `sanitized_output.png`.

REPLACE, TRANSLATE, ADD, and MIXED remain weak under the strict gate. Their
allowed-label violation and extra-component counts are still high. The result
is no longer explained by a data, palette, evaluator, or loader contract
failure.

## Decision

- C15 prompt/mask/action-specific diagnosis: allowed and recommended
- controlled 600-step continuation: not yet; revisit after C15, starting with REMOVE
- MIXED_80: completed
- 50/action expansion: blocked
- larger semantic_repair4 training: blocked

Exact next step: run C15 controlled prompt, mask, checkpoint-load, and
action-specific ablations using the valid step-300 checkpoints. Focus on
REPLACE allowed-label violations, TRANSLATE disconnected-mask behavior, and
ADD target reconstruction/extra components.

## Artifacts

- `reports/c14_4_palette_fixed_clean_training_result.json`
- `reports/c14_4_palette_fixed_{REMOVE,REPLACE,TRANSLATE,ADD}_20.json`
- `reports/c14_4_palette_fixed_MIXED_80.json`
- `reports/c14_4_loss_curves.csv`
- `reports/c14_4_loss_curves.png`
- `reports/c14_4_checkpoint_list.json`
- remote checkpoints under `outputs/qwen_semantic_repair4_palette_fixed_v1/`
- remote visual review under `outputs/manual_review/c14_4_palette_fixed_*/`
