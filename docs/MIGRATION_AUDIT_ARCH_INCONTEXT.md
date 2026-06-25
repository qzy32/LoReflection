# Migration Audit: Architecture In-Context v8 Route

Date: 2026-06-25

This is an audit-only report. No code, schemas, data, checkpoints, reports, or
training artifacts were modified, moved, deleted, or retrained while producing
this document.

## 0. Target Current Route

The formal current route for this audit is the v8 Architecture In-Context route:

```text
User instruction + Architecture JSON + frozen semantic registry
-> Goal State Constructor
-> Goal LoState
-> Prompt Compiler
-> compiled_text_prompt

Architecture JSON
-> palette-exact architecture renderer
-> architecture_condition_image

compiled_text_prompt + architecture_condition_image
-> Qwen-Image Architecture In-Context Control
-> initial semantic layout image
-> layout parser
-> layout JSON / scene JSON
-> Observed State Builder
-> Observed LoState
-> Goal-Observed Comparator / LoReview
-> Qwen3.5-VL StatePatch Editor
-> StatePatch Executor + Write-back Serializer
-> candidate layout JSON / scene JSON
-> rebuild Observed LoState
-> Verifier / Reviewer / AcceptanceController
```

The formal initial-generation method is:

```text
Qwen-Image Architecture In-Context Control
= DiffSynth-Studio Qwen-Image-In-Context-Control-Union LoRA
= compiled_text_prompt + architecture_condition_image
-> target_semantic_layout_image
```

Therefore, the old local-repair route
`RepairPlan -> mask_spec -> control_mask -> Qwen/DiffSynth inpaint` is no
longer the default mainline. It can remain only as a historical C12-C14
baseline, not as the active interface for VLM teammates.

## 1. Command Execution Notes

The requested commands were attempted from the Windows PowerShell workspace.

```text
tree -L 3
```

Result: Windows `tree.com` does not support `-L`; PowerShell returned
`Too many parameters - 3`. WSL `tree` was not installed. The structure summary
below is generated from filesystem enumeration instead.

```text
find . -maxdepth 4 -type f \( -name "*.py" ... \) | sort
```

Result: PowerShell treated `find` as the Windows command and failed on GNU-style
flags. WSL `find` ran, but paths under the Chinese username were mojibake. A
Python filesystem scan was used for reliable path names. It found 538
`.py/.md/.json/.yaml/.yml/.sh/.bat/.ipynb` files at max depth 4.

The three requested `rg` commands were run with native `rg.exe`. Raw output was
large, so this report records the file-level findings rather than embedding the
full terminal dump.

Summary counts:

| Pattern group | Files hit, all areas | Matches, all areas | Files hit excluding `outputs/`, `reports/`, `_archive/` | Matches excluding generated/history areas |
|---|---:|---:|---:|---:|
| Old RepairPlan / mask / inpaint terms | 251 | 4683 | 113 | 2436 |
| v8 Goal/Observed/StatePatch/architecture condition terms | 158 | 1472 | 63 | 844 |
| Geometry / pixel / size / bbox terms | 361 | 4426 | 112 | 924 |

Interpretation: the repository already contains strong v8 design documents, but
the files currently named as source-of-truth still point at the older
RepairPlan/mask_spec/semantic_repair4 route.

## A. Current Repository Structure Summary

Top-level directories and approximate file counts:

| Directory | Approx. file count | Audit note |
|---|---:|---|
| `_archive/` | 565 | Historical material. Old terms here are usually LEGACY_OK. |
| `artifacts/` | 19 | Contains `current_interface`, which is still old RepairPlan/mask_spec. Critical conflict. |
| `configs/` | 31 | Mostly C13/C14 DiffSynth inpaint training configs. Historical baseline, not v8 default. |
| `data_pipeline/` | 10 | Mixed: reusable skeletons plus old ControlNet repair-pair/SFT builders. Do not delete directly. |
| `diffusion/` | 3 | Old Qwen/DiffSynth inpaint training/inference wrappers. Historical baseline. |
| `docs/` | 59 | Contains both v8 authority docs and old C12-C14/current-interface docs. Needs source-of-truth rewrite. |
| `eval/` | 7 | Reusable evaluation code candidates. Needs later mapping to v8 metrics. |
| `examples/` | 29 | Toy samples still include RepairPlan/mask/controlnet examples. Legacy examples. |
| `loreflection/` | 22 | Strong reusable foundation: 3D-FRONT parser, semantic registry, top-down renderer, package builder. |
| `outputs/` | 804 | Generated experiment artifacts. Old terms here are mostly historical evidence. |
| `reports/` | 262 | Generated audit/training reports. Old terms here are mostly provenance. |
| `runtime/` | 8 | Mixed: closed-loop smoke, prompt builder, LoRAM/reviewer, old mask adapter. Needs migration, not deletion. |
| `schemas/` | 10 | Older schema mirrors. Needs legacy marking once v8 schemas exist. |
| `scripts/` | 26 | Mostly C13/C14 training command mirrors. Historical baseline. |
| `server_configs/` | 3 | Server path templates. Some old inpaint variables. Do not delete without confirming server use. |
| `tests/` | 38 | Current tests still enforce old RepairPlan/mask_spec contract. Critical conflict with v8 mainline. |
| `tools/` | 51 | Mixed: reusable validators/renderers and old semantic_repair4/evaluator/export tools. |
| `vlm/` | 4 | Contains placeholder old planner constructor/editor scripts. Needs migration to StatePatch. |

## B. Old Route Residuals By Severity

### CRITICAL

These files or packages present the old route as current/default, or enforce it
as the active interface.

| File or directory | Evidence | Why it matters | Suggested handling |
|---|---|---|---|
| `docs/CURRENT_PROJECT_STATE.md` | Current pipeline ends in `VLM Correction Planner -> RepairPlan -> semantic repair or parametric repair routing`; DiffSynth contract uses `I_bad`, `I_target`, `control_mask`, `blockwise_controlnet_*`. | This directly contradicts the v8 route and is named as source of truth. | Refactor into v8 source of truth. Move the old C12-C14 route into a clearly labeled historical section. |
| `README.md` | Lists Target LoState Constructor, VLM Correction Planner, RepairPlan, semantic_repair4, C13/C14 repair training as current. | New readers will learn the old pipeline as the main pipeline. | Rewrite around Architecture In-Context initial generation and StatePatch loop. Keep C14 as historical baseline. |
| `docs/START_HERE.md` | Current Protocol and Current Interface point to RepairPlan, mask_spec, VLM handoff, C13/C14 inpaint training. | This is the onboarding entry point. | Rewrite before asking VLM teammates to train against the new interface. |
| `PROGRESS.md` | Still tracks semantic_repair4 and C14 palette-fixed repair training as the active next-step family. | Progress status conflicts with v8 migration objective. | Update to say C14.4 is a historical/diagnostic baseline; next step is v8 migration. |
| `artifacts/current_interface/repairplan.schema.json` | Current output schema is RepairPlan. | Active interface is wrong for Qwen3.5-VL StatePatch Editor. | Do not delete yet. Add replacement `statepatch.schema.json`, then move old schema to legacy. |
| `artifacts/current_interface/mask_spec.schema.json` | Defines mask_spec components and pixel geometry. | mask_spec should not be the current VLM interface under v8. | Move to legacy only after new StatePatch/current schemas and tests exist. |
| `artifacts/current_interface/planner_input_context.schema.json` | Uses goal/observed/loreview plus `allowed_actions`, `execution_routing`, and RepairPlan output instruction pattern. | This is an old planner context, not the v8 StatePatch editor context. | Replace with StatePatch editor input context schema. |
| `artifacts/current_interface/manifest.json` | Declares current files as RepairPlan/mask_spec/current VLM handoff. | Makes old interface machine-readable as current. | Replace manifest after v8 interface is created. |
| `outputs/current_vlm_planner_handoff/` | Handoff package is named current and teaches ACTION_PROTOCOL / REPAIRPLAN_OUTPUT_SPEC. | VLM teammates will train old RepairPlan outputs. | Freeze as legacy handoff, create new `outputs/current_statepatch_editor_handoff/`. |
| `tools/validate_current_repairplan.py` | Current validator validates RepairPlan and mask_spec. | Current tests pass because they validate the old interface. | Keep until replacement exists; then rename to legacy validator. |
| `tests/test_current_*repairplan*`, `tests/test_current_mask_spec_schema.py`, `tests/test_current_vlm_handoff.py`, `tests/test_current_c12_manifest.py` | Tests assert old semantic_repair4 fields and mask_spec semantics. | CI currently protects old behavior. | Add v8 tests first, then move old tests to legacy/baseline test group or retire. |
| `docs/BEGINNER_CODE_READING_MANUAL.md` and `docs/BEGINNER_CODE_READING_BY_QUESTION.md` | Beginner path starts from RepairPlan, mask_spec, C12-C14 semantic repair. | New contributors will be pointed to the wrong route. | Rewrite for v8; keep old C14 sections as "historical semantic_repair4 baseline". |
| `docs/MODULE_AND_FOLDER_EXPLANATION.md` | Describes current folders around old schemas/configs/reports. | Folder guide conflicts with v8 route. | Update after v8 file layout is created. |
| `vlm/infer_planner.py` | Placeholder writes `repairplan-v1`, `action_type: INSERT`, and `mask_spec`. | Contains deprecated action alias and old output schema. | Replace with `infer_statepatch_editor.py`; keep old file only as legacy placeholder. |
| `tools/export_to_qwenvl_sft.py` | Prompt says "output a RepairPlan JSON with mask_spec and correction_prompt". | SFT target is old VLM Planner, not StatePatch. | Create new StatePatch SFT exporter; archive or rename this old exporter. |

### WARNING

These files are not necessarily wrong as historical or experimental assets, but
they should not be presented as the v8 default route.

| File or directory | Evidence | Suggested handling |
|---|---|---|
| `runtime/run_closed_loop.py` | No-model smoke uses Goal LoState, Observed LoState, prompt package, LoReview; does not implement StatePatch/write-back. | Refactor into v8 smoke after StatePatch schemas exist. Do not delete. |
| `runtime/prompt_builder.py` | Re-reads Architecture JSON and includes boundary vertex count and anchor ids in prompt package. | Refactor Prompt Compiler so text uses Goal LoState summary and does not leak geometry; architecture should enter via `architecture_condition_image`. |
| `runtime/mask_tensor_adapter.py` | Rasterizes `mask_spec` to binary `control_mask`. | Legacy semantic_repair4 component. Keep only as C12-C14 baseline. |
| `data_pipeline/build_controlnet_repair_pairs.py` | Builds `image`, `control_image`, `control_mask`, prompt pairs from RepairPlan. | Legacy C12-C14 data builder. Archive after v8 context-image builder exists. |
| `data_pipeline/build_planner_sft_data.py` | Builds old RepairPlan VLM SFT samples. | Replace with StatePatch SFT builder. |
| `data_pipeline/build_goal_lostate.py` | Toy rule-based Goal LoState skeleton. | Potentially reusable skeleton, but not production v8 Goal State Constructor. Rename/label as toy. |
| `data_pipeline/build_prompt_package.py` | Calls old `runtime.prompt_builder` with full Architecture JSON. | Refactor with v8 Prompt Compiler contract. |
| `data_pipeline/render_arch_condition.py` | Simple 512x512 PIL architecture condition renderer. | Keep as toy/reference only; prefer `loreflection.builders.scene_package_builder` for native pipeline. |
| `data_pipeline/render_gt_semantic_layout.py` | Toy fixed placements and furniture rendering from Goal LoState. | Not a v8 target renderer. Label as toy. |
| `diffusion/train_diffsynth_qwen_inpaint_lora.sh` | Trains Qwen/DiffSynth blockwise inpaint LoRA. | Keep as C14 baseline; not v8 Architecture In-Context training entry. |
| `diffusion/infer_diffsynth_qwen_inpaint_lora.py` and `diffusion/infer_diffsynth_qwen_inpaint_lora_sweep.py` | Inpaint inference route. | Keep for C14 analysis only. |
| `configs/c13_*`, `configs/c14_*`, `configs/c14_3_*` | `extra_inputs = blockwise_controlnet_image,blockwise_controlnet_inpaint_mask`. | Historical training configs; rename/relocate after new configs exist. |
| `scripts/c13_*`, `scripts/c14_*` | Server command mirrors for old semantic_repair4 training. | Keep as experiment provenance; not current training entry. |
| `README_SERVER.md` | Server docs mention InstantX / Qwen inpaint / C14 configs. | Update server README to distinguish old baseline from v8 Architecture In-Context training. |
| `docs/QWEN_DIFFSYNTH_TRAINING_CODE_GUIDE.md` and `docs/VIS01_*` | Explain old C14.4 blockwise inpaint training. | Keep as C14.4 visual/training audit, with deprecated-baseline header. |
| `tools/evaluate_c13_semantic_repair4_outputs.py` | Evaluates old raw/snapped/copyback/sanitized inpaint outputs. | Keep as C13/C14 evaluator; create separate v8 layout/state evaluator. |
| `tools/export_loreflection_to_diffsynth_inpaint.py` | Exports `blockwise_controlnet_*` metadata. | Legacy exporter; replace with `image,prompt,context_image` metadata exporter. |
| `tools/generate_vis01_c14_4_reports.py` | Generates C14.4 old-route reports. | Keep as report-generation provenance. |
| `examples/toy_samples/` | Contains `repairplan_v1.json`, `controlnet_sample_v1.json`, `mask_spec` examples. | Move to legacy examples after v8 toy examples exist. |
| `schemas/` | Older schema mirrors include repairplan/mask spec. | Mark as legacy or move once v8 schemas are installed. |
| `server_configs/paths*.env` | Server path templates include old inpaint model variables. | Do not delete. Update labels after v8 server path variables exist. |

### LEGACY_OK

These files mention old terms but are acceptable as historical evidence or as
explicit contrast with the v8 method.

| File or directory | Why OK | Suggested handling |
|---|---|---|
| `_archive/` | Already deprecated historical area. | Keep unless a separate archive pruning task is approved. |
| `reports/` | Generated provenance for C12-C14 and audits. | Keep; old terms here are expected evidence. |
| `outputs/` | Generated experiment outputs and manual review images. | Keep or archive by experiment policy, not by route migration audit. |
| `docs/C12_*`, `docs/C13_*`, `docs/C14_*`, `docs/VIS01_*` | C12-C14 experiment documentation. | Keep but prepend/maintain "historical semantic_repair4 baseline" status when docs are reorganized. |
| `01_论文详细文档更新_GoalObservedState_StatePatch中文版.md` | Defines v8 method and explicitly rejects old RepairPlan/mask_spec/full Edited LoState choices. | Treat as new authority candidate. |
| `02_LoState_GoalObserved_StatePatch设计文档_v8_ArchInContext中文版.md` | Defines Goal/Observed/StatePatch v8 and write-back to candidate layout/scene JSON. | Treat as new authority candidate. |
| `03_Benchmark更新_GoalObserved_StatePatch中文版.md` | Defines v8 benchmark and lists old inpainting repair as an ablation/baseline. | Keep as benchmark design. |
| `04_实验框架更新_GoalObserved_StatePatch中文版.md` | Experiment plan for v8. | Keep as new experiment framework. |
| `05_推动计划更新_GoalObserved_StatePatch中文版.md` | Migration roadmap. | Keep as planning document. |
| `06_Qwen-Image_Architecture_InContext_Control_方法与实验.md` | Explicitly states metadata should be `image,prompt,context_image` and extra input `context_image`. | Treat as new training-route authority. |

## C. Per-File Treatment Recommendations

| Object | Recommendation | Update references if moved? | Notes |
|---|---|---|---|
| `docs/CURRENT_PROJECT_STATE.md` | Refactor in place | Yes | Must become v8 source of truth. |
| `README.md`, `docs/START_HERE.md`, `PROGRESS.md` | Refactor in place | Yes | These are public/default entry points. |
| `artifacts/current_interface/repairplan.schema.json` | Rename/move to legacy after replacement | Yes | Do not remove until `statepatch.schema.json` and tests pass. |
| `artifacts/current_interface/mask_spec.schema.json` | Rename/move to legacy after replacement | Yes | Still needed to understand C14 artifacts. |
| `artifacts/current_interface/planner_input_context.schema.json` | Replace with StatePatch editor context | Yes | Old context can become `legacy_repairplan_planner_input_context.schema.json`. |
| `outputs/current_vlm_planner_handoff/` | Rename to legacy handoff after new handoff exists | Yes | Current name is misleading under v8. |
| `tools/validate_current_repairplan.py` | Rename to legacy validator after new validator exists | Yes | Avoid breaking existing tests before replacements are ready. |
| `vlm/infer_planner.py` | Refactor or replace | Yes | Must stop emitting `INSERT` and RepairPlan. |
| `runtime/run_closed_loop.py` | Refactor to v8 smoke | No deletion | It is a useful smoke-test skeleton. |
| `runtime/prompt_builder.py` | Refactor to v8 Prompt Compiler | Yes | Must avoid prompt geometry leakage and avoid re-parsing full user requirement. |
| `runtime/mask_tensor_adapter.py` | Keep as legacy baseline | Maybe | Only needed for C12-C14. |
| `data_pipeline/build_controlnet_repair_pairs.py` | Archive/rename legacy after new data builder exists | Yes | Old inpaint metadata builder. |
| `data_pipeline/build_planner_sft_data.py` | Archive/rename legacy after StatePatch SFT builder exists | Yes | Old RepairPlan SFT builder. |
| `data_pipeline/render_arch_condition.py` | Keep but mark toy | Maybe | Safe architecture-only renderer, but basic and 512px. |
| `data_pipeline/render_gt_semantic_layout.py` | Keep but mark toy | Maybe | Uses hard-coded furniture placements; not production target renderer. |
| `diffusion/*inpaint*` | Keep as C14 baseline | Maybe | Do not present as current v8 training route. |
| `configs/c13*`, `configs/c14*`, `scripts/c13*`, `scripts/c14*` | Keep as historical training baselines | Maybe | Useful for C14 provenance and comparison. |
| `examples/toy_samples/` | Archive after v8 examples exist | Yes | Current examples teach old RepairPlan/mask_spec. |
| `docs/QWEN_DIFFSYNTH_TRAINING_CODE_GUIDE.md`, `docs/VIS01_*` | Keep with historical C14 label | No | They answer "how C14.4 trained", not "what current route is". |

## D. Reusable Code Inventory

These should not be deleted during migration; they are useful foundations for
the v8 route.

| Reusable area | Files | Why reusable |
|---|---|---|
| Frozen semantic registry and palette | `artifacts/semantic_registry_v2/`, `loreflection/semantic_registry.py` | Needed for palette-exact layout images and category mappings. |
| 3D-FRONT / PlanJSON parsing | `loreflection/data/front3d/scene_parser.py`, `room_geometry.py`, `furniture_geometry.py`, `category_mapper.py`, `coordinate_transform.py` | Reads native scene geometry and maps raw categories. |
| Scene package builder | `loreflection/builders/scene_package_builder.py` | Builds native prototype packages, extracts architecture and furniture, renders images, records manifests. |
| Top-down renderer facade | `loreflection/rendering/topdown/renderer.py`, `architecture_renderer.py`, `semantic_rasterizer.py` | Can be reused for architecture condition and semantic layout rendering after contract cleanup. |
| Architecture condition validator | `tools/validate_architecture_condition.py` | Checks boundary, door/window/wall handling, and prevents architecture anchors from becoming furniture entities. |
| Native rendering audit | `tools/render_topdown_audit_v2.py` | Has contact sheets and separated architecture/furniture/overlay audit logic. |
| Semantic training dataset validator | `tools/validate_semantic_layout_training_dataset.py` | Already expects `architecture_condition_rgb.png` and semantic/furniture label artifacts; likely adaptable to v8 `image,prompt,context_image` validation. |
| LoRAM / review skeleton | `runtime/loram.py`, `runtime/track_a_geometry_review.py`, `runtime/track_b_semantic_review.py` | Can feed Goal-Observed Comparator / LoReview with refactoring. |
| Acceptance/controller skeleton | `runtime/acceptance_controller.py`, `eval/` | Candidate for v8 verifier/acceptance metrics. |

Architecture-condition risk note: `data_pipeline/render_arch_condition.py` appears
architecture-only. `loreflection.builders.scene_package_builder.render_architecture_condition_png`
is also designed around boundary/door/window/wall/floor metadata. The builder
also renders furniture semantic layouts separately. Keep a future invariant test
that `architecture_condition_image` contains no target furniture positions.

## E. New Files Needed For v8 Mainline

Recommended new current-interface files:

```text
artifacts/current_interface/statepatch.schema.json
artifacts/current_interface/statepatch_editor_input_context.schema.json
artifacts/current_interface/goal_lostate.schema.json
artifacts/current_interface/observed_lostate.schema.json
artifacts/current_interface/layout_json.schema.json
artifacts/current_interface/scene_json.schema.json
artifacts/current_interface/qwen_arch_incontext_metadata.schema.json
```

Recommended new handoff package:

```text
outputs/current_statepatch_editor_handoff/
  README_STATEPATCH_EDITOR_HANDOFF.md
  STATEPATCH_OUTPUT_SPEC.md
  INPUT_CONTEXT_SPEC.md
  planner_or_editor_sft_examples.jsonl
  schemas/
```

Recommended new tools/runtime modules:

```text
tools/validate_current_statepatch.py
tools/validate_arch_incontext_training_metadata.py
tools/audit_prompt_geometry_leakage.py
tools/audit_architecture_condition_no_furniture.py
tools/export_qwen_arch_incontext_metadata.py
runtime/goal_state_constructor.py
runtime/prompt_compiler.py
runtime/layout_parser.py
runtime/observed_state_builder.py
runtime/statepatch_executor.py
runtime/writeback_serializer.py
vlm/infer_statepatch_editor.py
```

Recommended new training/config path:

```text
configs/qwen_arch_incontext_control/
diffusion/train_qwen_arch_incontext_lora.sh
scripts/train_qwen_arch_incontext_*.sh
```

Recommended tests:

```text
tests/test_current_statepatch_schema.py
tests/test_current_statepatch_editor_handoff.py
tests/test_arch_incontext_metadata_requires_context_image.py
tests/test_prompt_compiler_no_geometry_leakage.py
tests/test_architecture_condition_excludes_target_furniture.py
tests/test_current_docs_do_not_present_repairplan_as_mainline.py
```

## F. Risk Files Not To Delete Directly

Do not delete these without an explicit migration step and replacement:

- `docs/CURRENT_PROJECT_STATE.md`
- `README.md`
- `docs/START_HERE.md`
- `PROGRESS.md`
- `README_SERVER.md`
- `artifacts/current_interface/*`
- `outputs/current_vlm_planner_handoff/`
- `tools/validate_current_repairplan.py`
- `tests/test_current_*`
- `data_pipeline/`
- `runtime/`
- `vlm/`
- `loreflection/`
- `tools/render_topdown_audit_v2.py`
- `tools/validate_architecture_condition.py`
- C12/C13/C14 reports, configs, scripts, and visual artifacts
- server path/config files
- any external data root or model checkpoint path

Reason: many of these are wrong as current-route documents, but they are still
referenced by tests, reports, docs, or experiment provenance. Migration should
replace and relabel first, then archive.

## G. Specific Old-Route Checks

### 1. RepairPlan / mask_spec / semantic_repair4 as main route

Confirmed in `docs/CURRENT_PROJECT_STATE.md`, `README.md`,
`docs/START_HERE.md`, `PROGRESS.md`, `artifacts/current_interface/`,
`outputs/current_vlm_planner_handoff/`, tests, and validator. This is CRITICAL.

### 2. Qwen/DiffSynth local inpaint for ADD/REMOVE/TRANSLATE/REPLACE

Confirmed in `diffusion/`, `configs/c13*`, `configs/c14*`, `scripts/c13*`,
`scripts/c14*`, C13/C14 docs, and VIS01 docs. This is acceptable only as a
historical C14 baseline.

### 3. `blockwise_controlnet_*`, `I_bad`, `I_target`, `control_mask`

Confirmed in C13/C14 configs, reports/docs, evaluator, exporters, and tests.
Must not be part of v8 Architecture In-Context training metadata. v8 metadata
should be `image,prompt,context_image,...`.

### 4. Target LoState Constructor / VLM Correction Planner / routing in default flow

Confirmed in old source-of-truth docs. Under v8, the route should be Goal State
Constructor -> Prompt Compiler -> Architecture In-Context initial generation,
then StatePatch editor for local repair.

### 5. `functional_relations`

Most hits are in v8 design docs as explicit rejected/changed terminology. These
are LEGACY_OK. If future schema files reintroduce `functional_relations` as an
independent table, reject it or rename according to v8 relation modeling.

### 6. Target LoState / Edited LoState as runtime state

`Edited LoState` appears mostly in v8 docs as a rejected alternative. Current
runtime still consumes Goal/Observed LoState JSON for smoke tests. The v8 route
allows Goal/Observed LoState as diagnostic views, but executable write-back must
target candidate layout JSON / scene JSON.

### 7. Executor writes LoState JSON directly

No mature current StatePatch executor was found. Existing `runtime/run_closed_loop.py`
writes only prompt/review smoke outputs. New executor/write-back serializer is
needed.

### 8. Goal State Constructor split into parser/planner/compiler/validator stages

The v8 design docs explicitly argue for a single Goal State Constructor module.
Existing `data_pipeline/build_goal_lostate.py` is a toy skeleton. No production
split pipeline was identified as active code, but old docs should be watched
when rewriting source-of-truth pages.

### 9. Prompt Compiler re-reads Architecture JSON

Confirmed in `runtime/prompt_builder.py` and `data_pipeline/build_prompt_package.py`.
The current prompt compiler reads full Architecture JSON and emits boundary
vertex count / anchor ids into prompt package. This is a WARNING for v8: text
should not become a second architecture parser. Architecture should be expressed
through `architecture_condition_image`.

### 10. Prompt leaks geometry terms

Geometry terms appear heavily in internal parser/renderer code and v8 docs. That
is acceptable. The concerning file is `runtime/prompt_builder.py`, which emits
text such as "inside the room boundary with N vertices" and "Respect
architectural anchor_id". Add a leakage test before production prompt generation.

### 11. Qwen training data only `image,prompt`, no `context_image`

Old C13/C14 inpaint training uses `image,prompt,blockwise_controlnet_image,
blockwise_controlnet_inpaint_mask`. v8 docs require `image,prompt,context_image`.
No complete current v8 metadata exporter was found.

### 12. `architecture_condition_image` renderer includes target furniture

The reusable architecture renderers appear intended to render architecture only.
Furniture rendering exists separately. This should still receive an explicit
unit test because the builder also creates semantic/furniture images in the same
package.

### 13. `target_semantic_layout_image` scope unclear

v8 docs say `image = target_semantic_layout_image`; this should be clarified in
the new schema as architecture + furniture fixed-palette semantic layout, unless
you intentionally define it as furniture-only. Current old docs sometimes use
"semantic layout" broadly and old C14 images are local repair targets.

## H. Next Migration Plan

1. Declare v8 as the source of truth in `docs/CURRENT_PROJECT_STATE.md`,
   `README.md`, `docs/START_HERE.md`, and `PROGRESS.md`.
2. Add new current interface schemas for StatePatch, StatePatch editor input,
   Goal LoState, Observed LoState, layout JSON / scene JSON, and
   Architecture In-Context metadata.
3. Add validators and tests for:
   - `image,prompt,context_image` metadata;
   - no prompt geometry leakage;
   - architecture condition excludes target furniture;
   - StatePatch writes back to candidate layout JSON / scene JSON;
   - old RepairPlan/mask_spec is not described as current.
4. Create `outputs/current_statepatch_editor_handoff/` for VLM teammates.
5. Move/rename old `outputs/current_vlm_planner_handoff/` and
   `tools/validate_current_repairplan.py` only after new handoff and tests pass.
6. Refactor `runtime/prompt_builder.py` into a v8 Prompt Compiler.
7. Build the v8 training metadata exporter:
   `target_semantic_layout_image + compiled_text_prompt + architecture_condition_image`.
8. Keep C13/C14 semantic_repair4/Qwen-DiffSynth-inpaint work as a labeled
   historical baseline and visual comparison, not as the default route.

## I. Bottom Line

The repository is mid-migration. The new v8 route is well specified in the
Chinese design documents, especially `01_*`, `02_*`, and `06_*`, but the
official entry-point files still teach and enforce the old C12-C14 RepairPlan /
mask_spec / semantic_repair4 pipeline. The highest-priority fix is not deleting
files; it is replacing the current interface and onboarding documents so the
active route becomes:

```text
Architecture In-Context initial generation + StatePatch write-back loop
```

with C14.4 retained as a deprecated but valuable experimental baseline.
