# Qwen/DiffSynth Training Code Guide

## 1. Current Training Target

The training target is Qwen-Image / DiffSynth Blockwise ControlNet Inpaint LoRA
for semantic_repair4: ADD, REMOVE, TRANSLATE, and REPLACE. ROTATE and SCALE are
not trained in this semantic repair path.

## 2. Training Data Directories

`outputs/semantic_repair4_overfit_dataset_v1/` is the C13 small overfit dataset.
The full folder is server-side; reports record the path as
`/wuqingyaoa800/qiuziyan/LoReflection/outputs/semantic_repair4_overfit_dataset_v1/`.

`outputs/semantic_repair4_medium_dataset_v1/` is the C14 medium diagnostic
dataset. Reports record 20 samples/action and 80 total rows.

Expected per-sample files are `I_bad.png`, `I_target.png`, `control_mask.png`,
`prompt.txt`, `repairplan_current.json`, `mask_spec_current.json`, and
`sample_summary.json`. Metadata files are `metadata_add.csv`,
`metadata_remove.csv`, `metadata_translate.csv`, `metadata_replace.csv`, and a
mixed metadata file.

## 3. metadata.csv Fields

| Field | File | Meaning | DiffSynth role | If wrong |
| --- | --- | --- | --- | --- |
| `image` | `I_target.png` | desired target layout | image target | trains wrong target |
| `blockwise_controlnet_image` | `I_bad.png` | flawed source layout | condition image | condition mismatch |
| `blockwise_controlnet_inpaint_mask` | `control_mask.png` | binary repaint mask | inpaint mask | wrong pixels edited |
| `prompt` | prompt text | correction instruction | text condition | action/category ambiguity |

## 4. Config Files

`configs/c13_semantic_repair4_overfit/` contains `add.yaml`, `remove.yaml`,
`translate.yaml`, `replace.yaml`, and `mixed.yaml`. C13 has 3 rows per single
action and 12 mixed rows. Explicit parameters include learning rate 1e-4, LoRA
rank 32, LoRA base model `dit`, max_pixels 262144, action-specific seeds, and
extra inputs for condition image and mask. Batch size, workers, and gradient
checkpointing are set in `scripts/c13_train_common.sh`.

`configs/c14_semantic_repair4_medium/` contains `add_20.yaml`, `remove_20.yaml`,
`translate_20.yaml`, `replace_20.yaml`, `mixed_80.yaml`, and a REMOVE memory
probe config. C14 has 20 rows/action and 80 mixed rows. Explicit parameters:
batch size 1, learning rate 1e-4, LoRA rank 32, max_pixels 262144, seed 4411,
num_workers 0, and gradient checkpointing true.

LoRA alpha/dropout, optimizer, scheduler, precision, and gradient accumulation
are not explicitly set in the local mirrors; document them as DiffSynth defaults
unless confirmed in the server `train.py`.

## 5. Training Scripts

`diffusion/train_diffsynth_qwen_inpaint_lora.sh` is a local server-only template
with placeholder paths.

`scripts/c13_train_common.sh` is the clearest local mirror of the real command:
it calls DiffSynth `examples/qwen_image/model_training/train.py`, passes data
keys `image,blockwise_controlnet_image,blockwise_controlnet_inpaint_mask`, sets
max_pixels 262144, batch size 1, num workers 0, learning rate 1e-4, LoRA rank
32, metrics JSONL path, extra inputs, gradient checkpointing, and output path.

`scripts/c13_train_add.sh`, `scripts/c13_train_remove.sh`,
`scripts/c13_train_translate.sh`, `scripts/c13_train_replace.sh`, and
`scripts/c13_train_mixed.sh` set action metadata and output roots.

`scripts/c14_train_remove_20.sh`, `scripts/c14_train_replace_20.sh`,
`scripts/c14_train_translate_20.sh`, `scripts/c14_train_add_20.sh`, and
`scripts/c14_train_mixed_80.sh` are server command mirrors. They default to a GPU
in the mirror, but C14.1 selected GPU2 dynamically.

True server training script:

`/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`

## 6. Training Results

C13 outputs are summarized in `reports/c13_overfit_*.json` and
`docs/C13_SEMANTIC_REPAIR4_OVERFIT.md`.

C14.1 outputs are summarized in:

- `reports/c14_1_autogpu_resume_result.json`
- `reports/c14_1_autogpu_image_eval_summary.json`
- `outputs/manual_review/c14_1_autogpu_loss_curves/`

Server checkpoints are under
`/wuqingyaoa800/qiuziyan/LoReflection/outputs/qwen_semantic_repair4_medium_v1/`.

## 7. Current Training State

C13 small overfit completed with PARTIAL gates. C14 data and loader passed.
C14.1 completed medium training but sampled step-300 evaluation still has
edit_success 0 and high allowed-label violations. The next step is diagnosis of
prompt, mask policy, and evaluator behavior, not larger training.
