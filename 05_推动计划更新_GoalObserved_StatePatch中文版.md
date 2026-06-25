<!-- LoReflection updated on 2026-06-25: Implementation plan for single-module Goal State Constructor and Observed State Builder -->

# 05 推动计划更新：Goal State Constructor + Qwen-Image Architecture In-Context Control + Observed State Builder + VLM StatePatch 闭环

## 0. 最终执行路线

本版最终执行路线：

```text
数据：SemLayoutDiff / 3D-FRONT / layout JSON + EditRoom-style editing pairs + 自建 LoReview repair pairs
目标构造：Goal State Constructor
初始生成：Qwen-Image In-Context-Control-Union LoRA（Architecture In-Context Control）
布局回读：已有 Qwen output parser → layout JSON 模块
当前状态构造：Observed State Builder
关系计算：Relation Measurer + Programmatic Verifier
问题诊断：Goal-Observed Comparator + LoRAM + LoReview
局部修复 / 编辑：Qwen3.5-VL StatePatch Editor
执行：StatePatch Executor 解析 Observed LoState 引用，Write-back Serializer 写入 candidate layout JSON / scene JSON
重建：Observed State Builder 从 candidate layout JSON / scene JSON 重新构建 Observed LoState
验证：Programmatic Verifier + VLM Reviewer
渲染：Deterministic Renderer
验收：AcceptanceController
```

明确不再把下面作为主线：

```text
DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint LoRA 作为局部修复主执行器。
InstantX/Qwen-Image-ControlNet-Inpainting 作为局部修复主路径。
RepairPlan + mask_spec + Mask Tensor Adapter 作为局部修改主接口。
VLM 直接输出完整 Edited LoState 并让系统完全相信。
functional_relations 作为与 object-object / object-architecture 平行的单独关系表。
Goal State Constructor 在主流程中拆成多个独立阶段。
```

---

---

## 最新统一口径：StatePatch 直接针对 Observed LoState 中的对象字段，但真正写回 layout JSON

本次进一步明确一个容易混淆的点：

```text
Observed LoState 是由 layout JSON / scene JSON 构建出来的诊断视图。
VLM 看到的是 Observed LoState，所以它输出的 StatePatch 应直接引用 Observed LoState 中的家具对象和数值字段。
Executor 不需要训练；它只做确定性的 target_ref 查表、字段映射、写回和失败回滚。
最终真正被修改、保存、渲染、导出和复测的是 candidate layout JSON / scene JSON。
```

因此，StatePatch 的最推荐形式不是完整 Edited LoState，也不是底层 layout JSON 路径，而是：

```json
{
  "action_type": "TRANSLATE",
  "target": {
    "target_ref": "obs:bed_001",
    "expected_category": "bed"
  },
  "state_field_updates": {
    "center_m": {
      "update_mode": "relative_delta",
      "delta_m": [0.6, 0.0]
    }
  },
  "reason": "bed overlaps the door clearance area",
  "constraints_to_satisfy": [
    "door_clearance_free",
    "inside_room",
    "no_collision"
  ],
  "protected_refs": [
    "obs:wardrobe_001",
    "obs:desk_001"
  ]
}
```

这里：

```text
target.target_ref：VLM 选择要修改的 Observed LoState 对象，例如 obs:bed_001。
state_field_updates：VLM 给出的局部数值字段更新，例如修改 center_m。
relative_delta：相对增量模式，表示在原值基础上加一个变化量。
delta_m：[0.6, 0.0] 表示在平面第一个坐标方向移动 0.6 米，第二个坐标不变。
```

执行链路统一为：

```text
VLM 输出 StatePatch，针对 Observed LoState 里的对象和字段
        ↓
Executor 在 Observed LoState 中解析 target.target_ref
        ↓
通过 source_object_id / source_json_path 找到 layout JSON / scene JSON 中的真实对象
        ↓
Write-back Serializer 将 state_field_updates 映射为底层 layout JSON 字段更新
        ↓
生成 candidate layout JSON / scene JSON
        ↓
Observed State Builder 从 candidate layout JSON / scene JSON 重新构建 candidate Observed LoState
        ↓
Programmatic Verifier + VLM Reviewer + AcceptanceController 判断 accept / rollback
```

最终分工：

```text
VLM 负责修复智能：改哪个家具、做什么动作、具体数值怎么变。
程序负责执行安全：查表定位、字段映射、写回 layout JSON、重建 Observed LoState、验证和回滚。
```

注意：这里的 `target_ref` 解析不是训练任务，而是确定性查表。Observed LoState 的每个家具实例必须保存 `source_object_id` / `source_json_path`，用于把 `obs:bed_001` 映射回 layout JSON / scene JSON 中的真实对象。如果找不到，系统返回 `PATCH_TARGET_NOT_FOUND`，不猜测、不模糊修改、不破坏非目标对象。

## 1. 模块划分

| 模块 | 采用代码 / 方法 | 作用 | 是否主线 | 是否需要训练 |
|---|---|---|---|---|
| Goal State Constructor | LLM/VLM + rule completion + schema validation | 从用户需求和建筑结构构造 Goal LoState | 是 | 可先不训练，后续 SFT |
| Goal label extractor | 规则抽取 | 从 3D-FRONT / layout JSON 自动构造 Goal LoState 训练标签 | 是 | 否 |
| Prompt Compiler | 自己实现 | Goal LoState → Qwen prompt | 是 | 否 |
| 初始生成器 | Qwen-Image In-Context-Control-Union LoRA（Architecture In-Context Control） | 生成初始 semantic layout | 是 | 已有 / 可继续优化 |
| Qwen output parser | 已有模块 | Qwen 结果 → layout JSON | 是 | 已有 |
| Observed State Builder | 自己实现 | layout JSON → Observed LoState | 是 | 否 |
| Relation Measurer | 自己实现 | 计算 measured_relations | 是 | 否 |
| Programmatic Verifier | 自己实现 | OOB / collision / door blocking / usability | 是 | 否 |
| LoRAM | 自己实现 | goal slot ↔ observed instance 对齐 | 是 | 否 / 可训练 |
| LoReview Generator | 自己实现 + VLM Track B | 问题归因和 target_ref 定位 | 是 | 可训练 |
| VLM StatePatch Editor | Qwen3.5 官方微调工具链 | 输出直接针对 Observed LoState 对象字段的局部 StatePatch | 是 | 是 |
| StatePatch Executor | 自己实现 | 确定性解析 target_ref，检查动作合法性，生成 candidate layout JSON 修改请求 | 是 | 否 |
| Write-back Serializer | 自己实现 | 将候选修改写回 candidate layout JSON / scene JSON | 是 | 否 |
| Deterministic Renderer | 自己实现 / 复用现有 renderer | LoState → semantic map | 是 | 否 |
| AcceptanceController | 自己实现 | accept / rollback / retry | 是 | 否 |
| Qwen-Image Inpainting | DiffSynth / InstantX | 旧路线对照或外观分支 | 否 | 非优先 |
| EditRoom | 数据和 baseline | editing pair / 动作空间 / 对照 | 是 | 不训练其 diffusion editor |
| SemLayoutDiff | 预处理和 baseline | 3D-FRONT 数据组织 / architecture-conditioned baseline | 是 | 不作为主方法 |

注意：

```text
不再把 Instruction Slot Parser、High-level Spatial Planner、Constraint Compiler、Goal Schema Validator 列为主线模块。
它们可以作为 Goal State Constructor 内部实现函数存在，但不作为独立 pipeline stage。
```

---

## 2. 需要新增/更新的代码


## Qwen-Image Architecture In-Context Control 实施计划

新增 / 更新代码：

```text
loreflection/render/render_architecture_condition.py
loreflection/qwen_arch_control/build_qwen_arch_control_dataset.py
loreflection/qwen_arch_control/write_metadata_csv.py
loreflection/qwen_arch_control/audit_palette_exact.py
loreflection/qwen_arch_control/audit_prompt_no_coordinate_leakage.py
loreflection/qwen_arch_control/run_diffsynth_incontext_lora.sh
loreflection/qwen_arch_control/infer_arch_incontext_control.py
loreflection/qwen_arch_control/parse_semantic_layout_to_json.py
```

数据生成顺序：

```text
1. canonicalize raw 3D-FRONT / PlanJSON / layout JSON。
2. 从 layout JSON + Architecture JSON 自动抽取 Goal LoState。
3. Prompt Compiler 生成 compiled_text_prompt。
4. Architecture JSON 渲染 architecture_condition_image。
5. layout JSON 渲染 target_semantic_layout_image。
6. 写 metadata.csv：image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs。
7. audit：palette exact、no coordinate leakage、required slot coverage、train/val/test scene split。
8. DiffSynth-Studio Qwen-Image-In-Context-Control-Union LoRA 训练。
9. 推理输出 semantic layout image。
10. parser 转 layout JSON / scene JSON。
11. 进入 Observed State Builder 与 StatePatch 闭环。
```

优先级：

```text
P0：生成 50–200 个小样本，验证 context_image 输入是否真正控制建筑结构。
P1：跑 full train/val split，比较 text-only baseline 与 architecture in-context control。
P2：加入 clearance region 图层消融。
P3：加入 downstream StatePatch 修复轮数与 Final Acceptance Rate 评价。
```

### 2.1 Goal State Constructor

```text
loreflection/goal/goal_state_constructor.py
loreflection/goal/goal_label_extractor.py
loreflection/goal/goal_constraint_rules.py
loreflection/goal/goal_schema_validator.py
loreflection/goal/prompt_compiler.py
```

核心函数：

```python
def construct_goal_state(
    user_instruction: str,
    architecture: dict,
    semantic_registry: dict,
    room_priors: dict | None = None,
) -> dict:
    """Return Goal LoState v2.

    This is the only online interface of Goal State Constructor.
    Internal slot parsing, constraint completion, and schema validation are implementation details.
    """
    pass
```

训练标签构造函数：

```python
def extract_goal_labels_from_layout(
    layout_json: dict,
    architecture: dict,
    semantic_registry: dict,
    room_type: str,
) -> dict:
    """Extract Goal LoState-style labels from existing layout JSON.

    This supports SFT / prompt examples for Goal State Constructor.
    """
    pass
```

---

### 2.2 Goal LoState schema

```text
schemas/goal_lostate_v2.schema.json
```

核心字段：

```text
schema_version
state_role
metadata
architecture_ref
semantic_registry_ref
room_type
furniture_slots
goal_constraints
verification_profile
prompt_compilation_policy
```

校验重点：

```text
Goal 不得包含 center_m / size_m / orientation_deg / footprint_m / bbox_m。
category 必须来自 semantic registry。
goal_constraints 只能属于 requirement / pairwise / region / global 四类。
required 约束必须尽量绑定 verification。
functional meaning 只能作为 intent_tag，不设 functional_relations 表。
```

---

### 2.3 Observed State Builder

```text
loreflection/observe/layout_json_to_lostate.py
loreflection/observe/geometry_builder.py
loreflection/observe/relation_measurer.py
loreflection/observe/programmatic_verifier.py
```

核心函数：

```python
def build_observed_state(
    layout_json: dict,
    architecture: dict,
    semantic_registry: dict,
    verification_profile: dict,
) -> dict:
    pass
```

输出：

```text
Observed LoState v2
```

---

### 2.4 Observed LoState schema

```text
schemas/observed_lostate_v2.schema.json
```

核心字段：

```text
schema_version
state_role
metadata
architecture_ref
semantic_registry_ref
room_type
furniture_instances
measured_relations
hard_constraint_evidence
```

---

### 2.5 Goal-Observed Comparator

```text
loreflection/review/loram_alignment.py
loreflection/review/constraint_satisfaction_checker.py
loreflection/review/loreview_generator.py
```

核心函数：

```python
def compare_goal_and_observed(
    goal_state: dict,
    observed_state: dict,
    architecture: dict,
) -> dict:
    pass
```

---

### 2.6 StatePatch schema / executor

```text
schemas/statepatch.schema.json
loreflection/patch/statepatch_executor.py
loreflection/patch/writeback_serializer.py
loreflection/patch/field_mapping.py
loreflection/patch/patch_execution_result.py
```

核心函数：

```python
def execute_statepatch_with_writeback(
    current_layout_json: dict,
    current_observed_state: dict,
    patch: dict,
    architecture: dict,
    semantic_registry: dict,
    field_mapping: dict,
) -> PatchExecutionResult:
    """Resolve VLM StatePatch over Observed LoState view,
    write the update to candidate layout JSON / scene JSON,
    rebuild Observed LoState from the candidate JSON,
    and return accept/fail with structured reasons.
    """
    pass
```

---

## 3. Goal State Constructor 实现计划

### 3.1 在线构造

在线只保留一个模块接口：

```text
User instruction + Architecture JSON + semantic registry
        ↓
Goal State Constructor
        ↓
Goal LoState
```

内部实现逻辑：

```text
1. 根据 user instruction 和 semantic registry 得到 furniture_slots。
2. 根据 Architecture JSON 自动补全门窗、墙体、clearance 相关 region constraints。
3. 根据 room priors / learned priors 补全常见 pairwise / region constraints。
4. 自动加入 global constraints，如 inside_room、no_collision、door_clearance_free、walkable_connected。
5. 做 schema validation，确保不输出家具坐标。
```

这五步是实现逻辑，不是论文主流程的五个阶段。

### 3.2 训练标签构造

从已有 layout JSON 构造 Goal LoState 标签：

```text
3D-FRONT / existing layout JSON
        ↓
Rule-based relation and constraint extraction
        ↓
Goal LoState label construction
        ↓
LLM prompt examples or SFT data
```

抽取规则：

```text
object category/count → furniture_slots

nightstand 与 bed edge_distance < threshold
→ pairwise: nightstand adjacent_to bed

sofa facing_angle_to_tv < threshold
→ pairwise: sofa facing TV

bed min_edge_distance_to_solid_wall < threshold
→ region: bed against solid wall

desk distance_to_window < threshold
→ region: desk near window

wardrobe front_clearance_depth > threshold
→ region: wardrobe front_accessible

no collision in layout
→ global: no_collision

all objects inside room
→ global: inside_room

walkable component count <= 1
→ global: walkable_connected
```

---

## 4. Observed State Builder 实现计划

### 4.1 Layout JSON Normalizer

功能：

```text
layout JSON → furniture_instances
```

规则：

```text
category → category_id
id → obs:instance_id
center/size/orientation/footprint 统一到 meter
缺 footprint 则重建旋转矩形
缺 bbox 则由 footprint 计算
```

### 4.2 Geometry Builder

功能：

```text
补齐 footprint_m / bbox_m / front_dir / right_dir
```

### 4.3 Relation Measurer

Object-object 关系：

```text
center_distance
edge_distance
overlap_area
relative_direction
facing_angle
parallel_angle
alignment_error
```

Object-region 关系：

```text
inside_room
distance_to_wall
distance_to_window
overlap_with_door_clearance
overlap_with_window_clearance
against_wall_distance
front_clearance_depth
side_clearance_width
```

Global evidence：

```text
collision
oob
door_window_blocking
circulation
furniture_use_clearance
```

---

## 5. VLM 训练任务

本版 shared Qwen3.5-VL LoRA 建议包含四个任务：

```text
[GOAL_STATE_CONSTRUCTION]
[SOFT_REVIEW]
[STATEPATCH_EDITING]
[PATCH_FEEDBACK_RETRY]
```

其中优先级：

```text
第一优先级：[STATEPATCH_EDITING]
第二优先级：[GOAL_STATE_CONSTRUCTION]
第三优先级：[SOFT_REVIEW]
第四优先级：[PATCH_FEEDBACK_RETRY]
```

---

## 6. SFT 数据格式

### 6.1 Goal State Construction SFT

```json
{
  "conversations": [
    {
      "from": "human",
      "value": "[GOAL_STATE_CONSTRUCTION]\nUser instruction={...}\nArchitecture summary={...}\nSemantic registry summary={...}\nPlease output a non-numeric Goal LoState JSON. Do not output object coordinates."
    },
    {
      "from": "gpt",
      "value": "{...Goal LoState JSON...}"
    }
  ]
}
```

### 6.2 StatePatch Editing SFT

```json
{
  "image": ["images/current_layout_0001.png"],
  "conversations": [
    {
      "from": "human",
      "value": "<image>\n[STATEPATCH_EDITING]\nArchitecture summary={...}\nGoal LoState={...}\nObserved LoState={...}\nLoReview={...}\nPlease output a local StatePatch JSON. Do not output mask_spec. Do not output a full Edited LoState."
    },
    {
      "from": "gpt",
      "value": "{...StatePatch JSON...}"
    }
  ]
}
```

---

## 7. 第一阶段里程碑

### Week 1：Schema freeze

```text
冻结 Goal LoState v2。
冻结 Observed LoState v2。
冻结 StatePatch schema。
冻结 goal_constraints 四类。
冻结 patch failure codes。
```

### Week 2：Goal label extractor + Goal Constructor 最小版

```text
实现 layout JSON → Goal label extractor。
实现 construct_goal_state() 最小规则版。
实现 semantic registry 校验。
实现 no-coordinate leakage 校验。
```

### Week 3：Observed State Builder

```text
实现 layout_json_to_lostate.py。
实现 Geometry Builder。
实现 object-object / object-region measured_relations。
实现 hard_constraint_evidence。
```

### Week 4：Comparator + LoReview

```text
实现 goal slot ↔ observed instance 对齐。
实现 constraint satisfaction checker。
实现 LoReview Generator。
```

### Week 5：StatePatch Executor + Write-back Serializer + Verifier

```text
实现 TRANSLATE / ROTATE / REMOVE。
实现 ADD / REPLACE 的最小版本。
实现 OOB / collision / door blocking。
实现 rollback log。
```

### Week 6：Renderer 统一

```text
LoState → fixed-palette semantic map。
确保训练 / 推理 / eval 颜色一致。
确保门窗墙不变色。
```

### Week 7：SFT 数据构造

```text
Goal State Construction SFT 数据。
StatePatch Editing SFT 数据。
LoReview repair pairs。
做 100-500 条 sanity check。
```

### Week 8：闭环集成

```text
Qwen-Image initial → layout JSON → observed → review → StatePatch → executor resolves target_ref → write-back candidate layout JSON → rebuild Observed LoState → verify → render。
跑 Ours-Initial vs Ours-Final。
```

---

## 8. 当前不建议优先做

```text
1. 不建议继续训练 DiffSynth/Qwen-Image Blockwise ControlNet Inpaint 作为局部布局修复主线。
2. 不建议先做复杂 constraint solver。
3. 不建议让 VLM 输出完整 Edited LoState。
4. 不建议一开始把 Goal State Constructor 拆成多个可训练子模型。
5. 不建议一开始做三模型独立 VLM。
6. 不建议一开始堆所有 external baselines。
7. 不建议继续围绕 mask_spec / control_mask 设计主实验。
```

---

## 9. 对照实验仍可保留

Qwen-Image inpainting 可以作为旧路线 baseline：

```text
Qwen-Image Inpainting Repair baseline：
用于证明 image-space local repair 容易产生非目标污染、色板漂移、旧位置残影或修复失败。
```

但它不再是主方法，不再是主要训练路线。

---

## 10. 最终一句话执行路线

```text
用 Goal State Constructor 生成非数值目标约束；用 Qwen-Image 只做初始布局；用 Observed State Builder 从 layout JSON 计算当前状态；用 Goal-Observed Comparator 生成 LoReview；用 VLM StatePatch 做局部修复；程序只做安全写入、验证、渲染和回滚。
```


---

## 10. Write-back 实现细节

本版必须新增一个明确的 write-back 层，避免“StatePatch 到底改 LoState JSON 还是 layout JSON”的歧义。

### 10.1 基本原则

```text
layout JSON / scene JSON 是可执行真值。
Observed LoState 是由 layout JSON / scene JSON 构建出的诊断视图。
VLM StatePatch 使用 Observed LoState 的 target_ref 表达修改对象。
程序执行时必须把 target_ref 映射回 layout JSON / scene JSON 的真实对象。
最终验收必须从 updated layout JSON / scene JSON 重新构建 Observed LoState。
```

### 10.2 必须实现的字段

Observed LoState 的每个 `furniture_instance` 必须包含：

```json
{
  "instance_id": "obs:bed_001",
  "source_object_id": "layout_bed_42",
  "source_json_path": "$.objects[0]",
  "category": "bed",
  "center_m": [1.4, 2.0],
  "size_m": [2.0, 1.5],
  "orientation_deg": 90
}
```

其中：

```text
instance_id：VLM 可读的 observed ref。
source_object_id：layout JSON / scene JSON 中的真实对象 ID。
source_json_path：该对象在 JSON 中的位置，用于确定性写回。
```

### 10.3 必须实现的字段映射表

```python
FIELD_MAPPING = {
    "center_m": ["position.x", "position.z"],
    "orientation_deg": "rotation_y_deg",
    "size_m": ["size.x", "size.z"],
    "category": "category",
    "asset_id": "asset_id",
}
```

实际字段名根据你现有 layout JSON schema 调整。没有映射的字段不得执行，返回 `PATCH_FIELD_MAPPING_FAIL`。

### 10.4 执行伪代码

```python
def execute_statepatch_with_writeback(
    current_layout_json,
    current_observed_state,
    patch,
    architecture,
    semantic_registry,
    field_mapping,
):
    validate_patch_schema(patch)
    target = resolve_target_ref(current_observed_state, patch["target"]["target_ref"])
    source_path = target["source_json_path"]

    candidate_layout_json = deepcopy(current_layout_json)
    layout_obj = get_by_json_path(candidate_layout_json, source_path)

    updates = translate_state_updates_to_layout_updates(
        patch.get("state_field_updates", {}),
        target,
        field_mapping,
    )
    apply_updates(layout_obj, updates)

    candidate_observed = build_observed_state(
        candidate_layout_json,
        architecture,
        semantic_registry,
        current_observed_state.get("verification_profile", {}),
    )

    verify_result = run_programmatic_verifier(candidate_observed, architecture)
    preserve_result = check_protected_refs(
        current_observed_state,
        candidate_observed,
        patch.get("protected_refs", []),
    )

    if verify_result.pass_all and preserve_result.pass_all:
        return PatchExecutionResult.accept(candidate_layout_json, candidate_observed)
    return PatchExecutionResult.fail_and_rollback(verify_result, preserve_result)
```
