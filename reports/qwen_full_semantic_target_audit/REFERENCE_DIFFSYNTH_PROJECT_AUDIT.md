# Reference DiffSynth Project Audit

## Finding

The reference project trains Qwen with `image + prompt + context_image`. Its room-layout target is a full semantic map: architecture/no-furniture condition plus furniture rendered on top.

## Evidence

- `examples/flux/model_training/metadata/build_flux_room_metadata_from_planjson.py`: renders `with_furn` and `no_furn`; writes `image = images/..._with_furn.png` and `kontext_images = kontext_images/..._no_furn.png`.
- `examples/qwen_image/model_training/metadata/build_qwen_room_metadata_from_flux.py`: converts FLUX metadata to Qwen metadata with `image`, `context_image`, `kontext_images`, and `prompt`.
- `scripts/render_qwen_input_with_furniture.py`: starts from palette-exact `*_qwen_input.png`, overlays furniture only on floor pixels, and checks door/window/wall/void pixels are unchanged.
- `examples/qwen_image/model_training/lora/Qwen-Image-SLDN-Room.sh`: trains DiffSynth Qwen with `--data_file_keys "image,context_image"` and `--extra_inputs "context_image"`.

## What can transfer to LoReflection

- Use `context_image` as architecture-only/no-furniture semantic condition.
- Use `image` as full semantic target when training a full-map output model.
- Keep palette-exact RGB and validate protected architecture pixels.
- Keep a furniture-only target as an auxiliary parser/evaluator artifact.

## What cannot transfer

- Category names, room taxonomy, and palette values cannot be copied because LoReflection uses its own frozen semantic registry and 3D-FRONT-derived data.
