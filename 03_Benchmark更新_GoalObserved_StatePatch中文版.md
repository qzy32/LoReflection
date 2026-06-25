<!-- LoReflection updated on 2026-06-25: Benchmark for single-module Goal State Constructor, Observed relation measurement, and StatePatch editing -->

# 03 Benchmark 更新：面向 Architecture In-Context 初始生成、Goal-Observed 状态对齐与 StatePatch 编辑的 LoReflection-Eval

## 0. 本版评价对象

本版 Benchmark 完整评价以下系统：

```text
Goal State Constructor
        +
Qwen-Image initial semantic generation
        +
Observed State Builder / Relation Measurer
        +
Goal-Observed Comparator / LoReview
        +
VLM StatePatch Editor
        +
StatePatch Executor / Write-back Serializer / Programmatic Verifier / AcceptanceController
```

注意：`Goal State Constructor` 在 Benchmark 中作为一个整体模块评价，不再拆成多个独立阶段。内部的 slot 抽取、约束补全、schema 校验只是实现细节。

评价重点：

```text
1. Goal State 是否正确表达用户需求和建筑约束；
2. Goal State Constructor 是否输出非数值、可验证的 Goal LoState；
3. Observed State 是否能从 layout JSON 正确构造；
4. measured_relations / hard_constraint_evidence 是否正确；
5. Goal constraints 与 Observed evidence 的比较是否能生成正确 LoReview；
6. VLM StatePatch 是否能直接针对 Observed LoState 对象字段给出局部数值修改，并通过 target_ref 查表、字段映射、write-back、rebuild、verification 完成安全执行。
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

## 1. Benchmark Package

每个样本构造：

```text
S_i = {
  A_i: architecture annotation,
  U_i: user instruction,
  R_i: semantic registry / palette / category set,
  G_i: target Goal LoState,
  Y_i: ground-truth object layout JSON,
  O_i: observed LoState built from Y_i,
  C_i: evaluation constraint specification,
  E_i: optional edit / repair tasks
}
```

其中：

```text
A_i：房间边界、门窗、墙体、clearance、坐标转换。
U_i：用户文本需求。
R_i：冻结语义注册表和 palette。
G_i：非数值目标约束状态，包含 furniture_slots / goal_constraints / verification_profile。
Y_i：真实或生成的对象级 layout JSON，包括类别、中心、尺寸、朝向、footprint。
O_i：从 layout JSON 计算得到的 Observed LoState。
C_i：评估约束，包括 requirement / pairwise / region / global 四类。
E_i：可选编辑或修复任务。
```

---

## 2. 核心评估维度

主维度更新为：

```text
Goal State Construction Quality
Observed State Construction Quality
Goal-Observed Review Quality
Initial Architecture-Controlled Generation Quality
Layout Generation Quality
Geometric Validity
Practical Usability
StatePatch Editing Quality
```

---

## 3. Goal State Construction Quality

评价 Goal State Constructor 是否能从 user instruction + Architecture JSON + semantic registry 得到合理的 Goal LoState。

### 3.1 Object Requirement Quality

```text
Slot Precision ↑
Slot Recall ↑
Slot F1 ↑
Required Count Accuracy ↑
Category Resolution Accuracy ↑
Semantic Registry Validity ↑
```

解释：

```text
Slot Precision：预测出的 furniture_slots 中有多少是正确目标。
Slot Recall：用户/标注中需要的目标 slot 有多少被提取出来。
Required Count Accuracy：数量是否正确。
Category Resolution Accuracy：类别是否正确映射到 semantic registry。
Semantic Registry Validity：是否没有编造 category。
```

### 3.2 Goal Constraint Quality

```text
Constraint Precision ↑
Constraint Recall ↑
Constraint F1 ↑
Constraint Kind Accuracy ↑
Predicate Accuracy ↑
Necessity Accuracy ↑
Verifier Binding Rate ↑
Invalid Constraint Rate ↓
Coordinate Leakage Rate ↓
```

按四类分别报告：

```text
requirement
pairwise
region
global
```

### 3.3 Goal State Validity

```text
Schema Validity ↑
Reference Validity ↑
Architecture Anchor Validity ↑
Semantic Registry Validity ↑
No-coordinate Compliance ↑
Prompt Hint Coverage ↑
```

其中：

```text
No-coordinate Compliance：
  Goal LoState 中不应出现 center_m / size_m / orientation_deg / footprint_m / bbox_m 等完整数值姿态字段。
```

### 3.4 Goal Label Extraction Quality

用于评价从 3D-FRONT / existing layout JSON 自动反推 Goal LoState 标签的质量。

```text
Auto-extracted Slot F1 ↑
Auto-extracted Pairwise Constraint F1 ↑
Auto-extracted Region Constraint F1 ↑
Auto-extracted Global Constraint F1 ↑
False Positive Constraint Rate ↓
Verifier Binding Coverage ↑
```

这一组指标用于证明训练标签构造可行，而不是评价线上 pipeline 的独立阶段。

---

## 4. Observed State Construction Quality

评价从 layout JSON 到 Observed LoState 的构造是否正确。

### 4.1 Geometry Normalization

```text
Instance Count Accuracy ↑
Category Accuracy ↑
Center Error ↓
Size Error ↓
Orientation Error ↓
Footprint IoU ↑
BBox IoU ↑
Unit Consistency Error ↓
```

### 4.2 Relation Measurement Accuracy

从 layout JSON 几何计算 measured_relations，按关系域报告：

```text
Object-object Relation Accuracy ↑
Object-region Relation Accuracy ↑
Global Evidence Accuracy ↑
```

更细指标：

```text
Pairwise Predicate Accuracy ↑
Edge Distance Error ↓
Center Distance Error ↓
Facing Angle Error ↓
Overlap Area Error ↓
Wall Distance Error ↓
Opening Clearance Error ↓
Furniture-use Clearance Error ↓
Walkable Component Count Accuracy ↑
```

### 4.3 Hard Constraint Evidence Accuracy

```text
OOB Detection F1 ↑
Collision Detection F1 ↑
Door Blocking Detection F1 ↑
Window Blocking Detection F1 ↑
Circulation Violation Detection F1 ↑
Furniture-use Violation Detection F1 ↑
```

---

## 5. Goal-Observed Review Quality

评价 LoReview 是否能准确比较 Goal constraints 和 Observed evidence。

```text
Issue Detection Precision ↑
Issue Detection Recall ↑
Issue Detection F1 ↑
Severity Accuracy ↑
Involved-ref Accuracy ↑
Constraint Matching Accuracy ↑
Suggested Action Type Accuracy ↑
Protected-ref Accuracy ↑
```

LoReview 是后续 StatePatch 的输入，所以这一组指标非常关键。

---

## 6. Layout Generation Quality


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

比较初始生成和闭环修复后的最终布局。

```text
Object Count F1 ↑
Goal Requirement SR ↑
Goal Pairwise Constraint SR ↑
Goal Region Constraint SR ↑
Goal Global Constraint SR ↑
OOB ↓
Collision ↓
Door / Window Blocking ↓
Practical Usability ↑
```

注意：本版不再使用 `Functional Relation SR` 作为主命名，因为功能不再是平行关系类。改为：

```text
Intent-aware Constraint SR
```

例如：

```text
viewing constraint satisfaction
sleeping_access constraint satisfaction
storage_access constraint satisfaction
entry_circulation constraint satisfaction
```

---

## 7. Geometric Validity

```text
OOB Rate ↓
Collision Rate ↓
Collision Area ↓
Door Clearance Violation ↓
Window Clearance Violation ↓
Opening Blocking Rate ↓
New Hard Error ↓
```

New Hard Error 用于修复或编辑任务：若 StatePatch 解决旧问题但引入新 hard errors，则计入失败。

---

## 8. Practical Usability

Practical Usability 继续作为本文亮点，但本版改成与 goal_constraints 的 verification 对齐。

```text
Opening Clearance Pass ↑
Circulation Clearance Pass ↑
Furniture-use Clearance Pass ↑
Reachability Pass ↑
Intent-aware Usability Pass ↑
```

示例：

```text
衣柜前是否有开门空间；
床侧是否有可通行空间；
桌椅是否有拉出空间；
沙发和电视距离/朝向是否合理；
门口是否被家具阻挡；
主通行区域是否连通。
```

---

## 9. StatePatch Editing Quality

### 9.1 Patch Validity and Write-back Validity

```text
JSON Validity ↑
Schema Validity ↑
Executable Rate ↑
Target Resolve Rate ↑
Source Mapping Rate ↑
Allowed-field Rate ↑
Field Mapping Rate ↑
Write-back Success Rate ↑
Rebuild Observed State Success Rate ↑
```

解释：

```text
Target Resolve Rate：StatePatch 中的 target_ref 能否在 Observed LoState 视图中解析到目标对象。
Source Mapping Rate：解析到的 observed object 能否通过 source_object_id / source_json_path 映射回 layout JSON / scene JSON 中的真实对象。
Field Mapping Rate：StatePatch 中的 state_field_updates 能否映射到底层 layout JSON 字段。
Write-back Success Rate：candidate layout JSON / scene JSON 是否成功写回。
Rebuild Observed State Success Rate：是否能从 candidate layout JSON / scene JSON 重新构建 Observed LoState。
```

### 9.2 Editing Success

```text
Edit Success ↑
Issue Resolution Rate ↑
Target Location Accuracy ↑
Target Orientation Accuracy ↑
Target Category Accuracy ↑
Constraint Improvement Rate ↑
```

### 9.3 Non-target Preservation

```text
NT-Pres ↑
Non-target Center Shift ↓
Non-target Orientation Shift ↓
Non-target Category Change ↓
Protected-ref Violation ↓
```

### 9.4 Verification and Rollback

```text
Patch Verify Pass ↑
Rollback Rate reported separately
Harmful Patch Rate ↓
No-improvement Patch Rate ↓
Avg. Repair Iterations ↓
Final Pass Rate ↑
```

Rollback Rate 不是单纯越低越好。若 VLM 输出错误 patch，系统能回滚，说明安全机制有效。因此主表同时报告 Harmful Patch Rate 和 Final Pass Rate。

---

## 10. 主实验表建议

### Table 1: Goal State Construction

| Method | Slot F1 ↑ | Count Acc ↑ | Constraint F1 ↑ | Predicate Acc ↑ | Verifier Binding ↑ | Coordinate Leakage ↓ | Invalid Constraint ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rule-only Goal Constructor | | | | | | | |
| LLM direct Goal JSON | | | | | | | |
| LLM constrained JSON + schema validation | | | | | | | |
| Ours Goal State Constructor | | | | | | | |

### Table 2: Goal Label Extraction from Layout JSON

| Method | Slot F1 ↑ | Pairwise F1 ↑ | Region F1 ↑ | Global F1 ↑ | False Positive ↓ | Verifier Binding ↑ |
|---|---:|---:|---:|---:|---:|---:|
| Manual template only | | | | | | |
| Rule extraction from layout JSON | | | | | | |
| Rule extraction + LLM cleanup | | | | | | |

### Table 3: Observed State Construction and Relation Measurement

| Method | Instance Acc ↑ | Footprint IoU ↑ | Pairwise Rel Acc ↑ | Region Rel Acc ↑ | Hard Evidence F1 ↑ | Clearance Error ↓ |
|---|---:|---:|---:|---:|---:|---:|
| layout JSON direct fields only | | | | | | |
| + Geometry Builder | | | | | | |
| + Relation Measurer | | | | | | |
| + Programmatic Verifier | | | | | | |

### Table 4: Goal-Observed Review Quality

| Method | Issue P ↑ | Issue R ↑ | Issue F1 ↑ | Severity Acc ↑ | Ref Acc ↑ | Constraint Match ↑ |
|---|---:|---:|---:|---:|---:|---:|
| Geometry-only reviewer | | | | | | |
| VLM free-form reviewer | | | | | | |
| Goal-Observed Comparator w/o LoRAM | | | | | | |
| Ours Comparator + LoRAM | | | | | | |

### Table 5: Layout Generation Quality

| Type | Method | CountF1 ↑ | Req.SR ↑ | Pairwise SR ↑ | Region SR ↑ | Global SR ↑ | OOB ↓ | Collision ↓ | Door/Window Blocking ↓ | Usability ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A2L | ATISS | | | | | | | | | |
| A2L | MiDiffusion | | | | | | | | | |
| A2L | SemLayoutDiff | | | | | | | | | |
| T2L | DirectLayout | | | | | | | | | |
| T2L | ReSpace | | | | | | | | | |
| TA2L | Qwen-Image-2512 text-only LoRA | | | | | | | | | |
| TA2L | Ours-Initial: Architecture In-Context Control |
| TA2L+Review | Ours-Final: Architecture In-Context Control + StatePatch | | | | | | | | | |

### Table 6: Review-guided Layout Editing Quality

| Method | Edit Success ↑ | Issue Resolution ↑ | Constraint Improvement ↑ | NT-Pres ↑ | Edit-induced Hard Error ↓ | Patch Exec. ↑ | Final Pass ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|
| EditRoom | | | | | | | |
| DirectLayout Re-generation | | | | | | | |
| Qwen-Image Inpainting Repair | | | | | | | |
| VLM Full Edited LoState | | | | | | | |
| VLM StatePatch w/o Verification | | | | | | | |
| Ours: StatePatch + Executor + Write-back + Verifier | | | | | | | |

---

## 11. 关键消融

```text
w/o semantic registry validation
w/o architecture-derived constraints
w/o relation-extraction training labels
w/o room priors
w/o verifier binding
w/o LoReview
w/o LoRAM
w/o Programmatic Verifier
w/o VLM Reviewer
w/o AcceptanceController
VLM Full Edited LoState instead of StatePatch
Qwen-Image inpainting repair instead of StatePatch
StatePatch without protected_refs
StatePatch without rollback
StatePatch without write-back serializer
StatePatch without rebuild-observe verification
```

注意：不再设置 `w/o high-level spatial plan` 作为主消融，因为本版不把 high-level plan 作为独立模块。若需要分析高层语义辅助，可作为 Goal Constructor 内部提示策略的附录实验。

---

## 12. 删除或降级的旧指标

以下指标不再作为主线：

```text
Mask Plan Validity
Mask Area Ratio
Invalid Mask Rate
Inpaint Success Rate
Non-target Mask IoU
Qwen-Image local repair sample quality
Functional Relation SR 作为独立关系类指标
High-level Spatial Plan Quality 作为独立主指标
```

这些可以作为旧路线或内部分析的附录，不进入新主方法。
