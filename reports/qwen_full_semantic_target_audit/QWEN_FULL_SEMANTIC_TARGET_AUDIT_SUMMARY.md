# Qwen Full Semantic Target Audit Summary

## 1. LoReflection current target

Current audited LoReflection `context_image` is architecture-only: it contains floor/door/void and no furniture. Current audited `target_semantic` is furniture-only over void/background: it contains furniture categories and void background, but no structural floor/door/window/wall pixels.

- target_interpretation: `furniture_only`
- context_contains_furniture: `False`
- target_contains_structural_architecture: `False`

## 2. Reference project target

The reference project uses Qwen In-Context training with `image + prompt + context_image`. Its `image` target is a full semantic map: architecture/no-furniture semantic base plus furniture overlay. Its `context_image` is the no-furniture architecture condition.

Key files:

- `examples/flux/model_training/metadata/build_flux_room_metadata_from_planjson.py`
- `examples/qwen_image/model_training/metadata/build_qwen_room_metadata_from_flux.py`
- `scripts/render_qwen_input_with_furniture.py`
- `examples/qwen_image/model_training/lora/Qwen-Image-SLDN-Room.sh`

## 3. Recommendation

LoReflection should add a controlled full-semantic target ablation before P1-1000. The proposed route is:

```text
context_image = architecture-only semantic condition
target_furniture_only = furniture-only semantic layer, kept for parser/eval
target_full_semantic = architecture semantic base + furniture semantic overlay
metadata image = target_full_semantic
Qwen output = full architecture+furniture semantic map
```

This does not mean deleting the current furniture-only route. The furniture-only target remains useful for parsing furniture connected components back into metric layout.

## 4. New rendering contract

The full target is composed by copying the architecture condition image and overlaying furniture semantic pixels from the furniture-only target. The renderer records forbidden architecture overwrite instead of silently repairing it.

Sample contract audit:

- status: `pass`
- architecture_preservation_rate_where_no_furniture: `1.0`
- forbidden_architecture_overwrite_rate: `0.0`
- palette_valid: `True`

## 5. Metadata design

Compatible DiffSynth metadata should keep the existing required fields and add an auxiliary furniture-only field:

```csv
image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs,target_furniture_only,target_full_semantic
```

For training, `image` should point to `target_full_semantic`. `target_furniture_only` is not a DiffSynth input; it is used by parser/evaluator/debugging.

## 6. Evaluation warning

Full semantic target evaluation must not rely only on full-image pixel agreement, because architecture pixels can dominate the score. Required metrics include architecture preservation, furniture precision/recall/F1, furniture class-color accuracy, forbidden architecture overwrite rate, and palette unknown rates.

## 7. Decision

- Train full_semantic_target ablation: yes, after user confirms.
- Start P1-1000 now: no. First compare current furniture-only route vs full-semantic target route on P1-small.

Review sample:

`reports/qwen_full_semantic_target_audit/sample_full_semantic_review/training_record_full_semantic.md`
