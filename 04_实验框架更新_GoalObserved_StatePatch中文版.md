<!-- LoReflection updated on 2026-06-25: Experiments for single-module Goal State Constructor, Observed State Builder, and StatePatch loop -->

# 04 实验框架更新：验证 Qwen-Image Architecture In-Context Control、Goal-Observed 状态对齐与 VLM StatePatch 局部修复

## 0. 实验要证明什么

本版实验要证明的不只是 VLM StatePatch 是否优于 Qwen-Image 局部重绘，而是完整证明以下链路成立：

```text
1. Goal State Constructor 能把 User instruction + Architecture JSON + semantic registry 转成不带家具坐标的 Goal LoState。
2. Goal State Constructor 可以作为单一模块工作，不需要在主流程中拆成多个独立阶段。
3. Goal LoState 中的 goal_constraints 能被 Prompt Compiler 编译为 compiled_text_prompt，并与 architecture_condition_image 共同指导 Qwen-Image Architecture In-Context Control 初始生成。
4. Qwen-Image Architecture In-Context Control 生成结果转成 layout JSON 后，Observed State Builder 能从 JSON 中构造带数值的 Observed LoState。
5. Relation Measurer 能从 layout JSON 几何中计算 measured_relations 和 hard_constraint_evidence。
6. Goal-Observed Comparator 能把目标约束和当前测量证据比较成 LoReview。
7. VLM StatePatch Editor 能根据 LoReview 直接针对 Observed LoState 中的对象字段输出局部数值修复动作。
8. StatePatch Executor 不需要训练；它能通过 Observed LoState 的 target_ref 确定性查表定位底层 layout object，并将 patch 写回 candidate layout JSON / scene JSON。
9. 系统必须从 updated layout JSON / scene JSON 重新构建 Observed LoState，再进行 Verifier / Reviewer / AcceptanceController 验收。
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

## 1. 主流程实验

```text
User instruction + Architecture JSON + semantic registry
        ↓
Goal State Constructor
        ↓
Goal LoState
        ↓
Prompt Compiler
        ↓
Qwen-Image Architecture In-Context Control initial generation
        ↓
layout JSON
        ↓
Observed State Builder
        ↓
Observed LoState
        ↓
Goal-Observed Comparator
        ↓
LoReview
        ↓
VLM StatePatch Editor
        ↓
StatePatch Executor resolves target_ref
        ↓
Write-back Serializer updates candidate layout JSON / scene JSON
        ↓
Observed State Builder rebuilds candidate Observed LoState
        ↓
Verifier + Reviewer + AcceptanceController
        ↓
Final layout
```

报告：

```text
Ours-Initial：Qwen-Image Architecture In-Context Control 初始生成结果。
Ours-Final：经过 Goal-Observed Review + VLM StatePatch 闭环修复后的最终结果。
```


## Qwen-Image Architecture In-Context Control 实验设计

### 目标问题

本组实验验证：

```text
Q1. Goal LoState 编译出的 prompt 是否能有效传递家具类别、数量和功能关系？
Q2. architecture_condition_image 是否显著提升门窗、墙、边界和 clearance 约束满足率？
Q3. Qwen-Image Architecture In-Context Control 是否比 text-only Qwen-Image 更适合作为后续 Observed LoState 与 StatePatch 闭环的初始布局来源？
```

### Baselines

```text
B0: Rule / heuristic layout baseline
B1: Qwen-Image text-only baseline
B2: Qwen-Image-2512 text-only LoRA
B3: Architecture-only control baseline
B4: Qwen-Image Architecture In-Context Control（本文主方法）
B5: Oracle prompt + architecture condition image
```

### Ablations

```text
A1 Prompt ablation:
  object-list prompt only
  object-list + pairwise relations
  object-list + pairwise + region guidance
  full Prompt Compiler prompt

A2 Architecture condition ablation:
  no architecture image
  room boundary only
  boundary + doors/windows
  boundary + doors/windows + clearance regions
  full architecture condition image

A3 Constraint routing ablation:
  all constraints in prompt
  required only
  required + preferred pairwise
  required + preferred + verifier-only separation

A4 Palette consistency ablation:
  fixed palette
  random palette
  enhanced visualization palette
```

### Metrics

```text
Image-level:
  Semantic IoU
  Category Pixel Accuracy
  Palette Validity Rate
  Unknown Color Rate
  Boundary Consistency

Object-level:
  Object Count F1
  Category Accuracy
  Missing Object Rate
  Extra Object Rate
  Object Area Ratio Error

Goal constraint:
  Requirement Success Rate
  Pairwise Relation Success Rate
  Region Constraint Success Rate
  Global Constraint Success Rate
  Required Constraint Pass Rate
  Preferred Constraint Score

Architecture constraint:
  Inside-room Pass Rate
  Out-of-bound Rate
  Door Clearance Violation Rate
  Window Clearance Violation Rate
  Door / Window Blocking Rate
  Wall-overlap Error
  Walkable Connectedness

Downstream closed-loop:
  Observed State Build Success Rate
  Verifier Pass Rate
  LoReview Issue Detection Rate
  StatePatch Repair Success Rate
  Final Acceptance Rate
  Average Repair Iterations
  Rollback Rate
```

预期结论：Text-only Qwen 更容易满足家具类别和数量，但容易忽略建筑边界、门窗和 clearance；Architecture In-Context Control 应显著降低 OOB、door/window blocking 和 clearance violation，并减少后续 StatePatch 修复轮数。

---

## 2. Experiment A：Goal State Constructor

### 2.1 目的

证明 Goal State Constructor 能作为单一模块正确构造：

```text
furniture_slots
goal_constraints
verification_profile
prompt_compilation_policy
```

并满足：

```text
不输出完整家具坐标；
不编造 semantic registry 之外的类别；
不把 functional_relations 作为独立关系表；
每条 required goal_constraint 尽量绑定 verification。
```

### 2.2 对照方法

```text
Rule-only Goal Constructor
LLM direct Goal JSON
LLM constrained JSON + schema validation
Ours Goal State Constructor
```

不再设置：

```text
LLM high-level plan only
High-level plan + rule Constraint Compiler
```

因为本版不把 high-level plan 或 compiler 写成主流程阶段。它们如果存在，只属于 Goal State Constructor 内部实现细节。

### 2.3 指标

```text
Slot F1
Count Accuracy
Category Resolution Accuracy
Constraint F1
Constraint Kind Accuracy
Predicate Accuracy
Necessity Accuracy
Architecture Reference Validity
Verifier Binding Rate
Invalid Constraint Rate
Coordinate Leakage Rate
```

### 2.4 消融

```text
w/o semantic registry validation
w/o architecture-derived constraints
w/o room priors
w/o relation-extraction training labels
w/o verification binding
w/o schema validation
```

### 2.5 训练标签构造实验

验证从真实布局自动构造 Goal 标签是否可靠：

```text
3D-FRONT / existing layout JSON
        ↓
rule-based extraction of object-object / object-region / global constraints
        ↓
Goal LoState labels
```

指标：

```text
Auto Slot F1
Pairwise Constraint F1
Region Constraint F1
Global Constraint F1
False Positive Constraint Rate
Verifier Binding Coverage
```

---

## 3. Experiment B：Observed State Builder / Relation Measurer

### 3.1 目的

证明从 layout JSON 可以确定性构造 Observed LoState，并计算关系。

### 3.2 输入

```text
layout JSON
Architecture JSON
semantic registry
verification_profile
```

### 3.3 输出

```text
Observed LoState
  - furniture_instances
  - measured_relations
  - hard_constraint_evidence
```

### 3.4 指标

```text
Instance Count Accuracy
Category Accuracy
Center Error
Size Error
Orientation Error
Footprint IoU
BBox IoU
Pairwise Relation Accuracy
Object-region Relation Accuracy
Hard Evidence F1
Opening Clearance Error
Collision Area Error
Walkable Component Count Accuracy
```

### 3.5 消融

```text
layout JSON direct fields only
+ Geometry Builder
+ Relation Measurer
+ Programmatic Verifier
```

这些是 Observed State Builder 内部实现层级，不影响主流程只保留一个 Observed State Builder 模块。

---

## 4. Experiment C：Goal-Observed Comparator / LoReview

### 4.1 目的

证明 LoReview 能正确定位 Goal constraints 和 Observed evidence 的差异。

### 4.2 指标

```text
Issue Detection Precision
Issue Detection Recall
Issue Detection F1
Severity Accuracy
Involved-ref Accuracy
Constraint Matching Accuracy
Suggested Action Type Accuracy
Protected-ref Accuracy
```

### 4.3 对照

```text
Geometry-only reviewer
LLM/VLM free-form reviewer
Goal-Observed Comparator without LoRAM
Ours Goal-Observed Comparator + LoRAM
```

---

## 5. Experiment D：Layout Generation Quality

### 5.1 目的

证明闭环反思和 StatePatch 修复能提升初始生成质量。

### 5.2 表格

| Type | Method | CountF1 ↑ | Req.SR ↑ | Pairwise SR ↑ | Region SR ↑ | Global SR ↑ | OOB ↓ | Collision ↓ | Door/Window Blocking ↓ | Usability ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A2L | ATISS | | | | | | | | | |
| A2L | MiDiffusion | | | | | | | | | |
| A2L | SemLayoutDiff | | | | | | | | | |
| T2L | DirectLayout | | | | | | | | | |
| T2L | ReSpace | | | | | | | | | |
| TA2L | Ours-Initial | | | | | | | | | |
| TA2L | Ours-Final | | | | | | | | | |

说明：

```text
Req.SR：requirement constraints satisfaction rate。
Pairwise SR：object-object constraints satisfaction rate。
Region SR：object-region constraints satisfaction rate。
Global SR：global constraints satisfaction rate。
Usability：由 intent-aware constraints 汇总得到。
```

---

## 6. Experiment E：Language-guided / Review-guided Layout Editing Quality

### 6.1 目的

证明 VLM StatePatch 编辑比全局重生成、Qwen-Image 局部重绘和完整 JSON 重写更稳。

| Method | Edit Success ↑ | Issue Resolution ↑ | Constraint Improvement ↑ | NT-Pres ↑ | Edit-induced Hard Error ↓ | Patch Exec. ↑ | Final Pass ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|
| EditRoom | | | | | | | |
| DirectLayout Re-generation | | | | | | | |
| Qwen-Image Inpainting Repair | | | | | | | |
| VLM Full Edited LoState | | | | | | | |
| VLM StatePatch w/o Verification | | | | | | | |
| Ours: StatePatch + Executor + Write-back + Verifier | | | | | | | |

说明：

```text
EditRoom 作为 editing protocol 和外部 baseline。
DirectLayout Re-generation 用于检验全局重生成是否破坏 non-target objects。
Qwen-Image Inpainting Repair 只作为旧路线对照，不再是主方法。
VLM Full Edited LoState 用于证明完整 JSON 重写风险。
Ours 使用 StatePatch 局部编辑和程序化验收。
```

---

## 7. Experiment F：Patch-level Diagnostics

| Method | JSON Valid ↑ | Schema Valid ↑ | Target Resolve ↑ | Source Mapping ↑ | Field Mapping ↑ | Write-back ↑ | Rebuild Obs. ↑ | Verify Pass ↑ | Rollback Rate | Harmful Patch ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VLM Full Edited LoState | | | | | | | |
| VLM StatePatch | | | | | | | | | | |
| VLM StatePatch + constrained decoding | | | | | | | | | | |
| VLM StatePatch + feedback retry | | | | | | | | | | |

---

### Experiment F 额外报告：write-back / rebuild consistency

本实验额外报告：

```text
Source Mapping Rate：target_ref 是否能映射到底层 layout object。
Field Mapping Rate：state_field_updates 是否能映射到 layout JSON 字段。
Write-back Success Rate：candidate layout JSON / scene JSON 是否成功生成。
Rebuild Observed State Success Rate：是否能从 candidate layout JSON / scene JSON 重建 Observed LoState。
Re-observed Verification Consistency：重建后的 Observed LoState 与直接候选状态的几何证据是否一致。
```

## 8. VLM StatePatch Editor 训练实验

### 8.1 数据来源

```text
EditRoom-style source-target editing pairs
+ 3D-FRONT / 3D-FUTURE 自动扰动 pairs
+ LoReview violation-driven repair pairs
```

### 8.2 数据转换

```text
current-before-edit layout JSON / scene JSON → Observed LoState
current-after-edit repaired layout JSON / scene JSON → rebuilt Observed LoState
before-after diff → StatePatch label
render current-before-edit layout JSON / scene JSON → semantic map
programmatic diff → LoReview
```

示例：

```text
current_before.center_m = [1.4, 2.0]
current_after_repaired.center_m = [2.0, 2.0]
```

转成：

```json
{
  "schema_version": "statepatch-v1.2",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
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
  }
}
```

### 8.3 VLM SFT 格式

```json
{
  "image": ["images/current_layout_0001.png"],
  "conversations": [
    {
      "from": "human",
      "value": "<image>\n[STATEPATCH_EDITING]\nArchitecture={...}\nGoal LoState={...}\nObserved LoState={...}\nLoReview={...}\nPlease output a local StatePatch JSON. Do not output a full Edited LoState."
    },
    {
      "from": "gpt",
      "value": "{...StatePatch JSON...}"
    }
  ]
}
```

---

## 9. Per-action Breakdown

主表报告平均值，附录按动作报告：

```text
ADD
REMOVE
TRANSLATE
ROTATE
SCALE
REPLACE
```

每类动作至少报告：

```text
Edit Success
Target Resolve
Patch Executable
No New Hard Error
NT-Pres
Final Pass
```

---

## 10. User Study

### 10.1 Generation User Study

比较 Ours-Initial 和 Ours-Final：

```text
哪个布局更符合文本？
哪个布局更满足门窗和建筑约束？
哪个布局更像真实可用房间？
哪个布局通行空间更合理？
```

### 10.2 Editing User Study

比较 EditRoom / Qwen-Image inpainting / VLM full rewrite / Ours StatePatch：

```text
哪个方法更准确完成编辑？
哪个方法更少破坏非目标家具？
哪个方法修复后更可用？
```

---

## 11. 成本分析

报告：

```text
Goal State Constructor tokens / time
Observed State Builder time
Relation Measurer time
Avg. VLM tokens per repair
Avg. patch retries
Avg. repair rounds
Avg. verifier time
Avg. renderer time
Total latency
```

---

## 12. 最终实验结论要证明

```text
Goal State Constructor 可以作为单一模块产生非数值、可验证 Goal LoState。
Observed State Builder 可以从 layout JSON 稳定计算当前测量状态。
Goal-Observed Comparator 可以把目标约束和当前证据变成可操作 LoReview。
VLM StatePatch + Executor + Write-back + Verifier 比 full rewrite / inpainting 更安全、更可控。
```
