# Palette Contract Audit

## Result

Partial local audit completed. Code support was added for:

- loading the frozen palette contract;
- extracting active palette entries from Goal LoState required counts;
- compiling `Architecture_Control` and `Palette_Control` into prompt text;
- auditing compiled prompts and class-color confusion when prediction outputs are available.

## Verified Locally

- Effective palette source: `artifacts/semantic_registry_v2/palette_frozen.json`.
- `Qwen` cannot directly read `palette_contract_ref`; that ref is for programmatic traceability.
- `Palette_Control` must be included in the actual metadata `prompt` string.

## Not Verified Locally

- P1 compiled metadata generation, because server `data/loreflection_qwen_arch_control_p1_small_metric_v2_*` directories are not present in this local snapshot.
- Prediction class-color confusion, because server quantized prediction outputs are not present locally.

