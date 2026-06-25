# Current Project State

## Current pipeline

User instruction + Architecture JSON
-> Target LoState Constructor
-> Goal LoState
-> Qwen-Image initial semantic layout generation
-> Programmatic State Observer
-> Observed LoState
-> Dual-Track Reviewer + LoRAM
-> LoReview
-> VLM Correction Planner
-> RepairPlan
-> semantic repair or parametric repair routing

## Action protocol

Planner-facing canonical actions:

- ADD
- REMOVE
- TRANSLATE
- ROTATE
- SCALE
- REPLACE

## Execution routing

semantic_repair4:

- ADD
- REMOVE
- TRANSLATE
- REPLACE

parametric_update:

- ROTATE
- SCALE

TRANSLATE is part of semantic_repair4. It must use old_region + new_region in mask_spec. If a RepairPlan carries a TRANSLATE parametric_delta, that field is bookkeeping only and does not change the execution route.

## DiffSynth contract

Only semantic_repair4 actions enter DiffSynth/Qwen-Image-Blockwise-ControlNet-Inpaint.

DiffSynth metadata:

- image = I_target
- blockwise_controlnet_image = I_bad
- blockwise_controlnet_inpaint_mask = binary control_mask
- prompt = correction_prompt

Mask:

- white/high = repaint
- black/low = preserve

## ROTATE / SCALE rule

ROTATE and SCALE are valid Planner actions. They do not enter Qwen semantic repair. They update structured layout fields through parametric_update.

ROTATE fields:

- target_instance_ref
- rotation_deg or new_yaw_rad
- geometry validation
- acceptance criteria

SCALE fields:

- target_instance_ref
- scale_xy or new_size
- geometry validation
- acceptance criteria

## EditRoom path

EditRoom official code/data are upstream editing-pair source. LoReflection does not reimplement EditRoom perturbation policy.

LoReflection conversion bridge converts EditRoom object-level before/after pairs into:

- I_bad
- I_target
- mask_spec
- binary control_mask
- RepairPlan
- correction_prompt
- DiffSynth metadata

Use this name only: EditRoom official-data conversion bridge.

## Current next step

C12 sanitizer has passed on the current semantic_repair4 sample set. C13 small Qwen/DiffSynth overfit has completed through 100-step checkpoints for ADD, REMOVE, TRANSLATE, REPLACE, and a 12-row mixed run.

C14 medium diagnostic data construction has also completed with 20 valid real converted EditRoom samples per semantic_repair4 action. DiffSynth `UnifiedDataset` dry-run passed for ADD, REMOVE, TRANSLATE, REPLACE, and MIXED_80. Medium training was attempted with REMOVE first, but the run stopped before step 1 because the selected server GPU did not have enough available memory, including a low-memory retry.

The current next executable step is to rerun the C14 REMOVE 20-step smoke on a GPU with enough free memory. Do not expand to 50/action or larger semantic_repair4 training until the 20/action medium smoke sequence runs.

Future C12/C13 inputs must not include ROTATE or SCALE in Qwen semantic repair.
