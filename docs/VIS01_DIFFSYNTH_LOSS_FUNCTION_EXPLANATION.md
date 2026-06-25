# VIS-01 DiffSynth Loss Function Explanation

## Where Loss Is Computed

The C14.4 train entry is `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/examples/qwen_image/model_training/train.py`.

- `train.py` lines 49-56 maps task `sft` / `sft:train` to `FlowMatchSFTLoss`.
- `train.py` lines 88-94 runs pipeline units and then calls the selected loss.
- The actual loss function is `/wuqingyaoa800/qiuziyan/DiffSynth-Studio/diffsynth/diffusion/loss.py`, `FlowMatchSFTLoss` lines 5-28.
- `loss.py` line 26 computes `torch.nn.functional.mse_loss(noise_pred.float(), training_target.float())`.
- `loss.py` line 27 multiplies by scheduler training weight.

## Objective

The training image `image = I_target` is encoded into latents. DiffSynth samples a random timestep, adds noise to those latents, asks the model to predict the scheduler training target, and applies MSE between prediction and target.

No explicit mask-only loss found; training appears to optimize the DiffSynth/Qwen diffusion objective on the training image conditioned by control image and inpaint mask.

## Input Flow

`UnifiedDataset` reads CSV rows. In `unified_dataset.py` lines 75-106, CSV metadata is loaded and `data_file_keys` are converted through image operators.

`training_module.py` lines 299-316 maps `blockwise_controlnet_image` and `blockwise_controlnet_inpaint_mask` into `ControlNetInput` under `blockwise_controlnet_inputs`.

`qwen_image.py` lines 514-526 preprocess control image and mask into blockwise ControlNet conditioning. Lines 784-808 inject blockwise ControlNet output into the DiT forward path.

## Trainable Modules

C14.4 passes `--lora_base_model dit` and does not pass `--trainable_models`. `training_module.py` line 239 freezes the pipeline, then lines 250-259 inject LoRA into `dit`. The blockwise ControlNet is not trained in C14.4.
