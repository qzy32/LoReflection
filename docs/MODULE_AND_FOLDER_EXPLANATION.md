# Module And Folder Explanation

This file describes the current v8 Architecture In-Context + StatePatch layout.

## Current Method Documents

- `docs/CURRENT_PROJECT_STATE.md`: current source of truth.
- `01_论文详细文档更新_GoalObservedState_StatePatch中文版.md`: method boundary.
- `02_LoState_GoalObserved_StatePatch设计文档_v8_ArchInContext中文版.md`: Goal/Observed/StatePatch design.
- `03_Benchmark更新_GoalObserved_StatePatch中文版.md`: benchmark and metrics.
- `04_实验框架更新_GoalObserved_StatePatch中文版.md`: experiment chain.
- `05_推动计划更新_GoalObserved_StatePatch中文版.md`: implementation order.
- `06_Qwen-Image_Architecture_InContext_Control_方法与实验.md`: Qwen initial generation interface.
- `docs/MIGRATION_AUDIT_ARCH_INCONTEXT.md`: old-route migration audit.

## Current Interface

`artifacts/current_interface/` now contains current v8 schemas:

- `statepatch.schema.json`
- `statepatch_editor_input_context.schema.json`
- `goal_lostate.schema.json`
- `observed_lostate.schema.json`
- `layout_json.schema.json`
- `scene_json.schema.json`
- `qwen_arch_incontext_metadata.schema.json`
- `manifest.json`

The old RepairPlan and mask schemas are kept only for the C12-C14 historical
baseline and are no longer declared as current mainline in `manifest.json`.

## Current Handoff

- `outputs/current_statepatch_editor_handoff/`: current VLM StatePatch editor
  handoff.
- `outputs/current_vlm_planner_handoff/`: legacy RepairPlan planner handoff for
  the historical C12-C14 semantic repair baseline.

## Runtime And Library Code

- `loreflection/semantic_registry.py`: frozen semantic registry loader.
- `loreflection/data/front3d/`: reusable 3D-FRONT parsing helpers.
- `loreflection/builders/scene_package_builder.py`: reusable scene package and
  rendering foundation.
- `loreflection/rendering/topdown/`: top-down renderer facades.
- `loreflection/goal/prompt_compiler.py`: current geometry-safe Prompt Compiler.
- `runtime/`: older smoke/review helpers plus components that can be migrated
  into the v8 StatePatch loop.

## Validators

- `tools/validate_current_statepatch.py`
- `tools/validate_arch_incontext_training_metadata.py`
- `tools/audit_prompt_geometry_leakage.py`
- `tools/audit_architecture_condition_no_furniture.py`
- `tools/validate_architecture_condition.py`

## Historical C12-C14 Baseline

The C12/C13/C14 docs, reports, configs, scripts, and visual artifacts are
retained for audit and comparison. They should be described as historical
semantic repair / inpaint experiments, not as the current LoReflection route.
