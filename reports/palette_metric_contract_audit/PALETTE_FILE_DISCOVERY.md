# Palette File Discovery

Current production registry loader is `loreflection/semantic_registry.py`. It reads:

- `artifacts/semantic_registry_v2/semantic_target_registry.json`
- `artifacts/semantic_registry_v2/palette_frozen.json`

No current `c2rgb.json` / `id2c.json` file was found in the local snapshot. The effective category-to-RGB contract is `palette_frozen.json`; `semantic_target_registry.json` provides IDs and category roles. Renderers, quantizer, parser and eval code read this through `load_registry()`.

Important contract point:

`Qwen` cannot directly read a `palette_contract_ref` JSON path. Qwen sees only `prompt`, `context_image`, and the supervised `image` target through DiffSynth. Therefore `palette_contract_ref` is for programmatic renderer/parser/verifier/audit traceability, while `Palette_Control` must be compiled into the prompt text if we want Qwen to receive that instruction.

## Discovered palette-like files

- `configs\category_mapping_3dfuture_to_palette_v1.json`
- `configs\palette_semlayoutdiff_native.json`
- `configs\palette_v1.json`
- `configs\palette_v2_qwenimage_candidate.json`
- `docs\C14_3_PALETTE_CONTRACT_REPAIR_AND_RERUN.md`
- `docs\C14_4_PALETTE_FIXED_CLEAN_TRAINING_RESULT.md`
- `docs\PALETTE_ALIAS_AND_3DFRONT_PARSER_AUDIT.md`
- `docs\PALETTE_RELIABILITY_EXPLANATION_V2.md`
- `docs\PALETTE_ROUNDTRIP_MULTICLASS_AUDIT.md`
- `docs\TRAINING_CATEGORY_AND_PALETTE_REGISTRY.md`
- `reports\active_38class_registry_palette_roundtrip_summary.json`
- `reports\c14_2_palette_contract_check.csv`
- `reports\c14_2_palette_contract_check.json`
- `reports\c14_2_palette_sanitizer_impact.csv`
- `reports\c14_2_palette_sanitizer_impact.json`
- `reports\c14_3_diffsynth_loader_dryrun_palette_fixed.json`
- `reports\c14_3_evaluator_selftest_palette_fixed.csv`
- `reports\c14_3_evaluator_selftest_palette_fixed.json`
- `reports\c14_3_invalidated_runs_due_to_palette_mismatch.json`
- `reports\c14_3_palette_contract_audit.csv`
- `reports\c14_3_palette_contract_audit.json`
- `reports\c14_3_palette_contract_repair_result.json`
- `reports\c14_3_palette_fixed_data_gate.csv`
- `reports\c14_3_palette_fixed_data_gate.json`
- `reports\c14_3_palette_fixed_distribution.json`
- `reports\c14_3_palette_fixed_medium_ADD_20.csv`
- `reports\c14_3_palette_fixed_medium_ADD_20.json`
- `reports\c14_3_palette_fixed_medium_MIXED_80.csv`
- `reports\c14_3_palette_fixed_medium_MIXED_80.json`
- `reports\c14_3_palette_fixed_medium_REMOVE_20.csv`
- `reports\c14_3_palette_fixed_medium_REMOVE_20.json`
- `reports\c14_3_palette_fixed_medium_REPLACE_20.csv`
- `reports\c14_3_palette_fixed_medium_REPLACE_20.json`
- `reports\c14_3_palette_fixed_medium_TRANSLATE_20.csv`
- `reports\c14_3_palette_fixed_medium_TRANSLATE_20.json`
- `reports\c14_3_palette_fix_samples.csv`
- `reports\c14_3_palette_mapping_old_to_frozen.json`
- `reports\c14_4_palette_fixed_ADD_20.csv`
- `reports\c14_4_palette_fixed_ADD_20.json`
- `reports\c14_4_palette_fixed_ADD_20_step100_eval.json`
- `reports\c14_4_palette_fixed_ADD_20_step300_eval.json`
- `reports\c14_4_palette_fixed_clean_training_result.json`
- `reports\c14_4_palette_fixed_MIXED_20_step100_eval.json`
- `reports\c14_4_palette_fixed_MIXED_20_step300_eval.json`
- `reports\c14_4_palette_fixed_MIXED_80.csv`
- `reports\c14_4_palette_fixed_MIXED_80.json`
- `reports\c14_4_palette_fixed_REMOVE_20.csv`
- `reports\c14_4_palette_fixed_REMOVE_20.json`
- `reports\c14_4_palette_fixed_REMOVE_20_step100_eval.json`
- `reports\c14_4_palette_fixed_REMOVE_20_step300_eval.json`
- `reports\c14_4_palette_fixed_REPLACE_20.csv`
- `reports\c14_4_palette_fixed_REPLACE_20.json`
- `reports\c14_4_palette_fixed_REPLACE_20_step100_eval.json`
- `reports\c14_4_palette_fixed_REPLACE_20_step300_eval.json`
- `reports\c14_4_palette_fixed_TRANSLATE_20.csv`
- `reports\c14_4_palette_fixed_TRANSLATE_20.json`
- `reports\c14_4_palette_fixed_TRANSLATE_20_step100_eval.json`
- `reports\c14_4_palette_fixed_TRANSLATE_20_step300_eval.json`
- `reports\category_palette_authority_trace.json`
- `reports\palette_roundtrip_and_perturbation.json`
- `reports\palette_roundtrip_multiclass_per_class.csv`
- `reports\palette_roundtrip_multiclass_results.json`
- `reports\palette_v2_atlas_roundtrip.json`
- `reports\palette_v2_closest_pairs.csv`
- `reports\palette_v2_distance_report.json`
- `reports\semlayoutdiff_final_palette.csv`
- `scripts\c14_3_wait_and_run_palette_fixed.sh`
- `scripts\c14_4_wait_and_run_palette_fixed_clean_training.sh`
- `scripts\c14_5_run_palette_fixed_severe_overfit1000.sh`
- `tests\test_palette_category_roundtrip.py`
- `tests\test_palette_v2_atlas_roundtrip.py`
- `tools\audit_palette_aliases.py`
- `tools\render_palette_category_atlas.py`
- `_archive\deprecated_20260622\outputs\palette_v2_validation\palette_38class_atlas.png`
- `_archive\deprecated_20260622\outputs\palette_v2_validation\palette_38class_distance_matrix.csv`
- `_archive\deprecated_20260622\outputs\val50_prototype_v1_arch_validated_visual_audit_semlayoutdiff_grounded\palette_legend.html`
- `_archive\deprecated_20260622\outputs\val50_prototype_v1_arch_validated_visual_audit_semlayoutdiff_grounded\palette_legend.json`
- `_archive\deprecated_20260622\outputs\val50_prototype_v1_arch_validated_visual_audit_semlayoutdiff_grounded\palette_legend.png`
- `_archive\deprecated_20260622\outputs\val50_prototype_v1_arch_validated_visual_audit_v2\palette_legend.html`
- `_archive\deprecated_20260622\outputs\val50_prototype_v1_arch_validated_visual_audit_v2\palette_legend.json`
