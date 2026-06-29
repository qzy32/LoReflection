# SemLayoutDiff Preprocess File Alignment Report

Reference root: `C:/Users/紫燕/Desktop/reference_repos/SemLayoutDiff`
Reference commit: `6b12bc4c42aa8377445af108093539073f0495c1`
LoReflection root: `C:/Users/紫燕/Desktop/LoReflection`

## SemLayoutDiff Findings

1. `preprocess/threed_front/datasets/parse_utils.py`
   - Builds `furniture_in_scene` from `data["furniture"]`.
   - Iterates `scene["room"]` and then `rr["children"]`.
   - Only if `child["ref"]` is in `furniture_in_scene`, the furniture is attached to that room.
   - The attached object carries `model_uid`, `model_jid`, and `model_info[jid]`.

2. `preprocess/threed_front/datasets/threed_front_scene.py`
   - `ModelInfo.from_file` loads 3D-FUTURE `model_info.json`.
   - `Asset.label` returns `model_info.category`.
   - `ThreedFutureModel.label` returns `self.model_info.label`, so the final model label is `model_info.category`.
   - `super-category` is stored metadata, not the concrete object label.

3. `preprocess/scripts/data_processor.py`
   - Uses explicit mapping files to convert room-specific ids to unified ids.
   - Updates `Updated_Bottom_label_map.png` and `Updated_Bottom_inst_anno.json` through mapping dictionaries.
   - It is not keyword matching over category + super-category + title.

4. `src/semlayoutdiff/apm/furniture_data_loader.py`
   - APM reads updated semantic label maps and annotation JSON.
   - Annotation category/mask/size/offset/orientation form APM supervision.

5. `src/semlayoutdiff/sldn/dataloader/front3d/front3d_fast.py`
   - SLDN reads unified semantic maps and label metadata.
   - Architecture condition follows semantic ids for floor/door/window in SemLayoutDiff's unified chain.

## LoReflection Divergence

The divergent file was `loreflection/qwen_arch_control/raw_3dfront_adapter.py`.
Previous behavior concatenated `model_info.category`, `model_info.super-category`, and furniture title/type, then used broad substring matching. This caused:

- Footstool / Sofastool / Bed End Stool / Stool -> double_bed
- Nightstand -> desk
- Wardrobe -> desk
- Bookcase / jewelry Armoire -> desk
- Shelf -> desk
- Drawer Chest / Corner cabinet -> desk

## Local Fix

Modified files:

- `loreflection/qwen_arch_control/raw_3dfront_adapter.py`
- `scripts/qwen_arch_control/audit_raw_3dfront_category_mapping.py`
- `scripts/qwen_arch_control/audit_renderer_input_category_boundary.py`
- `tests/qwen_arch_control/test_raw_3dfront_category_mapping.py`

Core policy:

- Primary source is `model_info.category`.
- `model_info.super-category` is audit metadata only and does not trigger primary mapping.
- Title fallback is allowed only when category is missing/unmapped.
- No naked `bed` -> `double_bed`.
- Unknown categories become `unknown_drop`.
- Room type hard gate keeps only bedroom/livingroom/diningroom; `LivingDiningRoom` is dropped and audited.

## Files intentionally not modified

- `loreflection/qwen_arch_control/semantic_topdown_renderer.py`
- `artifacts/semantic_registry_v2/palette_frozen.json`
- `artifacts/semantic_registry_v2/semantic_target_registry.json`
- `loreflection/qwen_arch_control/semantic_instance_extractor.py`
- Qwen train/inference scripts
- Prompt compiler

## Renderer Boundary

Category pollution occurs before rendering. The renderer consumes mapped semantic category/id and palette values. It does not read raw 3D-FUTURE `model_info.category`, `model_info.super-category`, or raw titles for category mapping.
