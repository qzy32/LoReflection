# LoState 设计文档 v1.4.9


> 核心结论：**LoState 不是普通 JSON layout，也不是 graph learning model，而是一种双角色、带关系注释的反思式状态语言（reflective state language）。它在 Qwen-Image 布局生成器与 Qwen2.5-VL 推理器之间建立可验证的信息中介，使生成布局能够被观察、比较、诊断、规划并修正。v1.4.5 进一步明确：局部修复主路径固定使用 Qwen-Image-ControlNet-Inpainting；mask 的空间语义规划由 Qwen2.5-VL Correction Planner 完成，程序层只负责把 VLM 输出的 `mask_spec` 栅格化为二值 `control_mask` 并做格式合法性检查。**

---

## 1. LoState 的最终定位

### 1.1 一句话定义

英文：

> **LoState is a dual-role, relation-annotated reflective state language that mediates verifiable communication between Qwen-Image and Qwen2.5-VL in a closed-loop layout generation and repair process.**

中文：

> **LoState 是一种双角色、带关系注释的反思式状态语言，用于在 Qwen-Image 与 Qwen2.5-VL 之间建立可验证的信息中介，并支撑闭环布局生成与修复。**

LoState 可以包含 graph-like relation edges，但论文中不应将其命名为 LoStateGraph。本文没有 GNN、graph diffusion、message passing 或 graph solver。LoState 的贡献在于 **state alignment and verification**，不是 graph learning。

更准确地说，LoState 不是单纯的工程接口，而是一个 **shared state language / communication substrate**：它把 Qwen-Image 生成的语义布局转写成 Qwen2.5-VL 可读、可比较、可规划的状态表达；同时又把 VLM 的诊断与修正规划约束回可执行的 RepairPlan 与 mask_spec。

### 1.3 LoState 是什么

LoState 是：

```text
1. Goal specification 的结构化承载；
2. Observed geometry 的结构化回读；
3. Goal–Observed 对齐的公共 schema；
4. Dual-Track State Reviewer 的输入接口；
5. LoReview 进行双轨状态审查时的状态依据；
6. Qwen2.5-VL Correction Planner 生成 RepairPlan 与 mask_spec 时的状态上下文；
7. Mask Tensor Adapter 解析 instance_ref / bbox / polygon 时的几何来源；
8. AcceptanceController 进行再观察验收时的状态比较依据。
```

注意第 6 点是 Qwen2.5-VL Planner 读取 LoState 与 LoReview 后输出 RepairPlan + VLM Mask Plan。

### 1.4 三个关键词

| 关键词 | 含义 | 对应模块 |
|---|---|---|
| Observable | 生成图像被 State Observer 回读为结构化状态 | State Observer |
| Comparable | Goal 与 Observed 共享 schema，可进行结构化对齐 | LoReview / Reviewer |
| Correctable | 差异被 VLM Planner 转为 RepairPlan + mask_spec，驱动局部修复 | Correction Planner / Qwen-Image-ControlNet-Inpainting |

---

## 2. 命名策略：正文自然，schema 边界清楚


LoState
semantic layout image
top-down semantic map
semantic layout loop
reflective layout loop
layout correction loop
VLM-guided mask planning
binary control mask
Qwen-Image-ControlNet-Inpainting



> We use LoState as the paper-facing name for the reflective state language. When necessary, we refer to the top-down semantic layout state as LoState2D to distinguish it from the Final3DState produced after APM lifting.

---

## 3. LoState 与整体管线的接口位置

### 3.1 LoReflection 

```text
User Instruction U
+ Architecture JSON A
+ optional architecture layout image
        ↓
Target LoState Constructor (Qwen2.5-VL)
        ↓
Goal LoState G
        ↓
Prompt / Condition Builder
        ↓
Qwen-Image / ControlNet initial generation
        ↓
Semantic Layout Image I⁰
        ↓
State Observer
        ↓
Observed LoState Ŝ⁰
        ↓
Dual-Track State Reviewer
        ↓
LoRAM slot-instance alignment
        ↓
LoReview R⁰
        ↓
Violation Ranking
        ↓
Qwen2.5-VL Correction Planner
        ↓
RepairPlan a⁰ + VLM Mask Plan mspec⁰
        ↓
Mask Tensor Adapter
        ↓
binary control_mask M⁰ + descriptive correction_prompt P⁰
        ↓
Qwen-Image-ControlNet-Inpainting
        ↓
Semantic Layout Image I¹
        ↓
Re-observe → Re-verify
        ↓
Acceptance / Rollback
        ↓
Semantic layout loop passes
        ↓
APM lifting
        ↓
Final3DState
```

### 3.2 每个结构的职责

| 结构 | 输入 | 输出 | 职责 |
|---|---|---|---|
| Architecture JSON | 数据预处理 | 不可变建筑条件 | 存储墙、门、窗、边界、clearance、坐标变换 |
| Goal LoState | 用户需求 + Architecture | 目标状态 | 描述“应该满足什么” |
| Observed LoState | 生成图像 + Architecture | 观测状态 | 描述“实际生成了什么” |
| LoReview | Goal + Observed + 图像 | 双轨状态审查报告 | 通过 LoRAM 对齐 Goal slots 与 Observed instances，并汇总几何违规、语义问题、观测问题与修复建议 |
| Violation Ranking | LoReview | ordered violations | 决定优先修哪个问题 |
| Qwen2.5-VL Correction Planner | Goal + Observed + LoReview + 图像 | RepairPlan + mask_spec | 规划修什么、为什么修、mask 覆盖哪里、最终状态 prompt 如何写 |
| RepairPlan | Planner 输出 | 修正动作规格 | 结构化记录 action_type、target_ref、protected_refs、mask_spec、prompt、验收条件 |
| Mask Tensor Adapter | RepairPlan.mask_spec + Observed geometry | binary control_mask | 只做栅格化、二值化、尺寸/面积/格式合法性检查 |
| Qwen-Image-ControlNet-Inpainting | control_image + control_mask + prompt | 修复图像 | 固定局部修复执行器 |
| AcceptanceController | old/new LoReview + old/new Observed | accept / rollback | 确保闭环修复有效且不引入新硬错误 |
| Final3DState | 通过验证的 LoState + APM | 三维状态 | 恢复 height、z_offset、retrieved_model_id 等 |

### 3.3 LoState 的边界

LoState 本体只包括：

Goal LoState
Observed LoState


不包括：

```text
LoReview
RepairPlan
mask_spec
control_mask
Revision Log
Runtime Tensor Cache
Final3DState 
```

原因：

```text
LoState 表示状态；
LoReview 表示状态审查报告；
RepairPlan 表示 VLM Planner 的动作与 mask 规划输出；
control_mask 是 Qwen-Image-ControlNet-Inpainting 的执行层输入；
Revision Log 是闭环轨迹记录；
Final3DState 是 APM 后的三维状态。
```

---

## 4. Architecture JSON：不可变外部条件

Architecture JSON 是外部不可变条件，不属于 LoState 可变状态。

### 4.1 Architecture JSON 示例

```json
{
  "schema_version": "architecture-v1.0",
  "architecture_id": "arch_0001",
  "room_type": "bedroom",
  "coordinate_system": {
    "layout_plane": "xz",
    "vertical_axis": "y",
    "unit": "meter",
    "orientation_convention": {
      "zero_degree_axis": "+x",
      "positive_direction": "counter_clockwise",
      "unit": "degree"
    }
  },
  "coordinate_transforms": [
    {
      "transform_id": "xz_to_image_001",
      "from": "world_xz_meter",
      "to": "image_pixel",
      "image_size_px": [1024, 1024],
      "matrix_3x3": [
        [243.8, 0, 0],
        [0, 284.4, 0],
        [0, 0, 1]
      ]
    }
  ],
  "boundary": {
    "polygon_m": [[0, 0], [4.2, 0], [4.2, 3.6], [0, 3.6]]
  },
  "anchors": [
    {
      "anchor_id": "wall_south",
      "anchor_type": "wall",
      "segment_m": [[0, 0], [4.2, 0]]
    },
    {
      "anchor_id": "door_001",
      "anchor_type": "door",
      "bbox_m": [1.65, 0.0, 2.55, 0.15],
      "swing": "inward"
    },
    {
      "anchor_id": "window_001",
      "anchor_type": "window",
      "bbox_m": [1.35, 3.45, 2.85, 3.60]
    },
    {
      "anchor_id": "door_001_clearance",
      "anchor_type": "clearance",
      "polygon_m": [[1.5, 0], [2.7, 0], [2.7, 1.0], [1.5, 1.0]]
    }
  ]
}
```

### 4.2 LoState 中如何引用 Architecture

```json
"architecture_ref": {
  "architecture_id": "arch_0001",
  "coordinate_transform_id": "xz_to_image_001"
}
```

通过 `arch:` 前缀引用建筑锚点：

```json
"object": "arch:window_001"
```

```text
against a wall away from arch:door_001
near arch:window_001
avoid arch:door_001_clearance
```

---

## 5. Metadata 与 Semantic Registry

### 5.1 最小 metadata 字段

Goal LoState 与 Observed LoState 都建议包含最小 metadata：

```json
"metadata": {
  "task_id": "bedroom_case_001",
  "role": "observed",
  "repair_round": 0,
  "source_image": "layout_round0.png"
}
```

字段解释：

| 字段 | 含义 |
|---|---|
| `task_id` | 同一个布局任务的样本 ID，用于把 Goal、Observed、LoReview、RepairPlan、mask_spec 和修复结果关联起来 |
| `role` | 当前状态角色，例如 `goal` 或 `observed` |
| `repair_round` | 第几轮闭环修复；初始生成结果为 0，第一次修复后为 1 |
| `source_image` | 当前 Observed LoState 对应的语义布局图像 |

`state_id`、`previous_observed_id`、`created_at` 等字段可在工程实现或 revision log 中保留，但不建议放在主文示例里制造理解负担。

### 5.2 repair_round 

`repair_round` 表示闭环修复轮次，不是视频帧。例如：

```text
repair_round = 0：初始生成图 I⁰ 的观测状态
repair_round = 1：第一次局部修复后 I¹ 的观测状态
repair_round = 2：第二次局部修复后 I² 的观测状态
```


### 5.3 semantic_registry_ref

Goal 与 Observed 必须共享同一套语义注册表：

```json
"semantic_registry_ref": {
  "palette_id": "indoor_palette_v1",
  "category_set": "indoor_furniture_categories_v1",
  "relation_set": "layout_relations_v1"
}
```

它首先解决三个基础问题：

```text
1. 固定色板中的颜色对应什么家具类别；
2. category_id 与 category name 如何映射；
3. near / adjacent_to / facing / blocks 等关系词如何解释和检查。
```

例如，Qwen-Image 输出 fixed-palette semantic map 后，Programmatic State Observer 需要通过 registry 知道：

```text
RGB = #AABBCC → category_id = 9 → category = nightstand
```

否则 Observed LoState 中的类别字段就不稳定。

因此，`semantic_registry_ref` 的基础职责不是预测生成模型会犯什么错，而是提供整个 LoReflection 闭环共享的语义坐标系：

```text
palette consistency
category consistency
relation-vocabulary consistency
```


### 5.4 LoRAM dynamic candidate mining：回读后动态发现候选

本文不引入独立的 `category_matching_profile` 或 `category_prior_registry`。原因是：LoRAM 不应依赖一张预定义的“类别兼容表”或“类别属性先验表”来猜测生成模型可能犯什么错。`wrong-category candidate` 应当在 Observed LoState 回读之后，由当前布局证据动态发现。

`semantic_registry_ref` 只承担最基础的语义字典职责：

```text
1. palette color → category_id / category name；
2. 合法 category set；
3. relation vocabulary；
4. relation predicate 的几何计算定义。
```

也就是说，registry 只告诉系统：

```text
这个颜色 / category_id 是什么类别；
near / adjacent_to / overlap / blocks 等关系如何被计算；
哪些类别名是合法的。
```

它不告诉系统：

```text
nightstand 可以匹配 small_table；
chair 可以匹配 nightstand；
某类家具会被生成模型错成另一类家具。
```

真正的候选判断发生在 LoRAM 中。对于每个 Goal slot `s_i` 和 Observed instance `o_j`，LoRAM 先判断：

```text
category(s_i) == category(o_j) ?
```

如果类别完全一致，则它是：

```text
exact candidate
```

如果类别不一致，LoRAM 不会马上把 `o_j` 判为 extra，而是继续检查当前布局证据：

```text
1. o_j 是否满足该 slot 的核心 desired relation；
2. o_j 是否处在合理的 anchor / free-floor 区域；
3. o_j 的面积、长宽比、mask 形状是否与该 slot 的局部需求相容；
4. o_j 是否违反 hard constraints；
5. 当前是否存在更合理的 exact candidate；
6. 是否需要 VLM reviewer 判断其功能语义。
```

只有当这些证据共同支持时，`o_j` 才会被动态标记为：

```text
wrong-category candidate
```

否则，它仍然会被视为 unmatched observed instance，并进入：

```text
entity_extra
```

对应 Goal slot 若无其他合理匹配，则进入：

```text
entity_missing
```

#### 示例：small_table 是否能作为 nightstand 的候选

Goal 中有：

```text
slot_nightstand_1:
  category = nightstand
  desired_relation = adjacent_to slot_bed_1
```

Observed 中有：

```text
small_table_1:
  category = small_table
  measured_relation = adjacent_to bed_1
  area = small
```

LoRAM 的判断不是：

```text
registry 预先说 small_table 可以替代 nightstand。
```

而是：

```text
small_table_1 类别不等于 nightstand；
但它位于 bed_1 旁边；
它的面积适合作为床边小家具；
它满足 slot_nightstand_1 的核心 relation evidence；
当前没有更合理的 exact nightstand candidate。
```

因此，LoRAM 可以动态生成：

```text
slot_nightstand_1 ↔ small_table_1
match_type = wrong-category candidate
LoReview issue = category_mismatch
Planner action = REPLACE
```

如果同样的 `small_table_1` 出现在房间中央，离 bed 很远，或尺寸明显不合理，则它不会成为 nightstand 的候选，而会更可能被判为：

```text
small_table_1 → entity_extra
slot_nightstand_1 → entity_missing
```

#### 示例：chair 在床边为什么通常不能当 nightstand

如果 Observed 中有：

```text
chair_1 adjacent_to bed_1
```

它虽然满足 `adjacent_to bed` 这一条关系，但类别语义和形状证据仍然不支持它承担 nightstand 的角色。LoRAM 应结合 bbox、mask、面积、形状、类别名与 VLM semantic review 判断：

```text
chair_1 是座椅类实例；
它不应因为在床边就被强行解释成 nightstand；
关系证据可以支持候选，但不能单独推翻类别语义边界。
```

因此更合理的输出是：

```text
slot_nightstand_1 → entity_missing
chair_1 → entity_extra
```

除非 VLM reviewer 在特殊上下文下明确判断该实例确实承担了目标 slot 的功能角色，否则不应将其作为 wrong-category candidate。

一句话：

```text
wrong-category candidate 不是 registry 预先指定出来的；
它是 LoRAM 在回读 Observed LoState 后，
根据类别不一致但空间 / 尺寸 / 关系证据强这一事实动态挖掘出来的。
```


---

## 6. Goal LoState 

Goal LoState 描述“应该满足什么”。

### 6.1 Goal LoState 示例

```json
{
  "schema_version": "lostate-v1.4",
  "state_role": "goal",
  "metadata": {
    "task_id": "bedroom_case_001",
    "state_id": "goal_bedroom_case_001",
    "repair_round": 0,
    "previous_observed_id": null,
    "created_by": "Qwen2.5-VL_TargetConstructor"
  },
  "architecture_ref": {
    "architecture_id": "arch_0001",
    "coordinate_transform_id": "xz_to_image_001"
  },
  "semantic_registry_ref": {
    "semantic_registry_version": "indoor_furniture_ontology_v1",
    "palette_id": "indoor_palette_v1",
    "category_set": "indoor_furniture_categories_v1",
    "relation_set": "layout_relations_v1"
  },
  "room_type": "bedroom",
  "furniture_slots": [
    {
      "slot_id": "slot_bed_1",
      "category": "bed",
      "category_id": 5,
      "required": true,
      "count": 1,
      "generation_hints": [
        {
          "description": "against a wall away from the door",
          "anchor_refs": ["arch:door_001"]
        }
      ],
      "avoid_refs": ["arch:door_001_clearance"],
      "source": "user_instruction"
    },
    {
      "slot_id": "slot_nightstand_1",
      "category": "nightstand",
      "category_id": 9,
      "required": true,
      "count": 1,
      "generation_hints": [
        {
          "description": "beside the bed",
          "anchor_refs": ["slot_bed_1"]
        }
      ],
      "avoid_refs": [],
      "source": "room_prior"
    }
  ],
  "desired_relations": [
    {
      "relation_id": "dr_nightstand_bed",
      "subject": "slot_nightstand_1",
      "predicate": "adjacent_to",
      "object": "slot_bed_1",
      "object_kind": "furniture_slot",
      "params": {
        "max_distance_m": 0.5,
        "allowed_sides": ["left", "right"]
      },
      "necessity": "required",
      "verification": "geometric_then_semantic",
      "source": "room_prior"
    }
  ],
  "verification_profile": {
    "hard_checks": [
      {
        "check_id": "hc_count_match",
        "type": "count_match",
        "scope": "furniture_slots",
        "severity": "error"
      },
      {
        "check_id": "hc_no_collision",
        "type": "no_collision",
        "scope": "all_furniture_instances",
        "severity": "error"
      },
      {
        "check_id": "hc_within_boundary",
        "type": "within_boundary",
        "scope": "all_furniture_instances",
        "severity": "error"
      },
      {
        "check_id": "hc_no_clearance_overlap",
        "type": "no_clearance_overlap",
        "scope": "architecture_clearance_regions",
        "severity": "error"
      },
      {
        "check_id": "hc_non_target_preservation",
        "type": "non_target_preservation",
        "scope": "editing_non_target_instances",
        "severity": "error"
      }
    ]
  }
}
```

### 6.2 Goal LoState 不应该做什么

Goal 不应该：

```
1. 给每个家具输出刚性坐标；
2. 凭空生成不存在的 arch anchor；
3. 把 room prior 强行变成用户要求；
4. 把所有软关系都变成 required；
5. 输出最终 mask；
6. 输出 RepairPlan；
7. 输出 mask_spec；
8. 输出 Qwen-Image-ControlNet-Inpainting 参数。
```
---

## 7. Observed LoState 

Observed LoState 描述“实际生成了什么”。

### 7.1 Observed LoState 示例

```json
{
  "schema_version": "lostate-v1.4",
  "state_role": "observed",
  "metadata": {
    "task_id": "bedroom_case_001",
    "state_id": "obs_bedroom_case_001_round0",
    "repair_round": 0,
    "previous_observed_id": null,
    "created_by": "ProgrammaticStateObserver"
  },
  "architecture_ref": {
    "architecture_id": "arch_0001",
    "coordinate_transform_id": "xz_to_image_001"
  },
  "semantic_registry_ref": {
    "semantic_registry_version": "indoor_furniture_ontology_v1",
    "palette_id": "indoor_palette_v1",
    "category_set": "indoor_furniture_categories_v1",
    "relation_set": "layout_relations_v1"
  },
  "observation_source": {
    "type": "top_down_semantic_map",
    "image_size_px": [1024, 1024],
    "parser": "fixed_palette_connected_components",
    "palette_id": "indoor_palette_v1",
    "source_image_id": "layout_round0.png"
  },
  "runtime_cache_ref": {
    "label_map_id": "cache_label_map_round0",
    "instance_map_id": "cache_instance_map_round0",
    "free_floor_mask_id": "cache_free_floor_round0"
  },
  "furniture_instances": [
    {
      "instance_id": "bed_1",
      "category": "bed",
      "category_id": 5,
      "tracking_id": "bed_track_001",
      "edit_role": "target_or_new",
      "geometry": {
        "bbox_px": [214, 312, 420, 820],
        "bbox_m": [0.89, 1.30, 1.75, 3.42],
        "mask": {
          "encoding": "rle",
          "rle": "...",
          "optional_png_ref": "mask_bed_1.png"
        },
        "centroid_m": [1.32, 2.36],
        "orientation_deg": 90,
        "orientation_confidence": 0.84,
        "area_m2": 1.82
      },
      "parser_confidence": 0.99
    }
  ],
  "measured_relations": [
    {
      "relation_id": "mr_desk_window",
      "subject": "desk_1",
      "predicate": "near",
      "object": "arch:window_001",
      "object_kind": "architecture_anchor",
      "measured": {
        "distance_m": 0.72
      },
      "satisfies_goal_relation": "dr_desk_window",
      "confidence": 0.98,
      "computed_by": "geometry"
    }
  ],
  "hard_constraint_evidence": [
    {
      "evidence_id": "ev_bed_clearance_001",
      "check_id": "hc_no_clearance_overlap",
      "type": "clearance_overlap",
      "subject": "bed_1",
      "object": "arch:door_001_clearance",
      "measured": {
        "overlap_area_m2": 0.12
      },
      "threshold": {
        "max_overlap_area_m2": 0.0
      },
      "status": "violated",
      "computed_by": "geometry"
    }
  ],
  "parser_status": {
    "parser_confidence": 0.99,
    "notes": []
  }
}
```

### 7.2 Observed 字段解释

Observed 中的家具是实际生成结果里的 instance，不是目标 slot。Observed 包含 `bbox_px`、`bbox_m`、`mask`、`centroid_m`、`orientation_deg`、`area_m2` 等几何事实，这些来自固定色板语义图的程序化解析，而不是 VLM 对自然图像的主观 bbox 猜测。

### 7.3 Observed LoState 不应该做什么

Observed 不应该：

```
1. 重新解释用户目标；
2. 修改 Architecture JSON；
3. 把 evidence 直接写成 diagnosis；
4. 让 VLM 覆盖程序计算出的 bbox / mask；
5. 存储完整 dense relation graph；
6. 存储 Qwen-Image-ControlNet-Inpainting 的 control_mask；
7. 存储 RepairPlan / mask_spec；
8. 存储最终 3D asset id。
```

注意：Observed 中的 object mask 是“观测到的家具实例 mask”；RepairPlan 中的 `mask_spec` 是“VLM 规划的编辑区域”。二者不是同一个概念。

---

## 8. Programmatic State Observer：只负责状态回读

State Observer 不再设计为“两阶段 Layer”。在本文任务中，Qwen-Image 输出的是 **2D fixed-palette semantic layout 色块图**，因此状态回读应尽可能保持确定性：由程序通过色板和连通域分析从图像中提取 label map、instance map、家具实例、bbox、mask、centroid、area、orientation 与基础几何证据。

换言之，**State Observer 只回答“实际生成了什么”**，不回答“哪里不合理”或“应该怎么修”。语义审查、软约束判断和修正规划统一交给后续的 Dual-Track State Reviewer 与 Qwen2.5-VL Planner。

### 8.1 输入

```text
Semantic Layout Image Iᵗ
+ Architecture JSON A
+ palette / category registry
```

### 8.2 输出

```text
Observed LoState Ŝᵗ
  - label map / instance map references
  - furniture_instances
  - bbox / mask / centroid / area / orientation
  - measured geometric relations
  - hard geometry evidence
  - parser_confidence
```

### 8.3 核心原则

```text
1. bbox、mask、centroid、collision、boundary、clearance 等几何事实由程序计算；
2. VLM 不作为 State Observer 的第二层，不覆盖 Observed LoState 中的几何真值；
3. 如果需要语义判断，进入 Dual-Track State Reviewer；
4. 如果需要修复区域规划，进入 Qwen2.5-VL Correction Planner。
```

```text
Programmatic State Observer
→ Observed LoState
→ Dual-Track State Reviewer
→ LoReview
```

---

## 9. LoReview ：双轨状态审查报告

LoReview 不属于 LoState 本体。它不是 State Observer 的重复输出，而是 **Dual-Track State Reviewer** 在读取 Goal LoState 与 Observed LoState 后产生的审查报告。

### 9.2 Dual-Track State Reviewer

#### Track A：Programmatic Geometry Review

Track A 使用 Observed LoState 中的程序化几何事实进行确定性检查：

```text
1. count match；
2. collision；
3. within boundary；
4. clearance overlap；
5. non-target preservation；
6. measured relation threshold。
```

#### Track B：Qwen2.5-VL Semantic Review

Track B 不修改几何真值，而是基于 Goal、Observed、Track A 摘要和当前语义图进行语义审查：

```text
1. 功能关系是否合理；
2. 动线是否合理；
3. 文化/使用常识是否满足；
4. 是否存在视觉或空间语义违和；
5. 是否建议 REOBSERVE 或直接进入修复规划。
```

### 9.3 LoReview 输入输出

输入：

```text
Goal LoState G
+ Observed LoState Ŝᵏ
+ optional previous Observed LoState Ŝᵏ⁻¹ for editing preservation
+ current semantic layout image Iᵏ
```

输出：

```text
LoReview Rᵏ
```

### 9.4 LoReview 内容类别

```text
1. entity_issue：缺失、多余、类别错误；
2. relation_issue：desired relation 未满足；
3. hard_geometry_issue：碰撞、越界、clearance overlap；
4. soft_semantic_issue：功能、动线、文化偏好问题；
5. preservation_issue：编辑任务中非目标对象漂移；
6. observation_issue：解析置信度不足，需要 REOBSERVE。
```

### 9.5 LoRAM: Partial Fused Relation-Aware Matching

在 LoReview 能够判断布局问题之前，系统必须先回答一个基础问题：**Goal LoState 中的 furniture slot 应该对应 Observed LoState 中的哪个 furniture instance？** 这不是简单的类别计数问题，因为 observed instance 可能类别不完全正确但满足目标 slot 的空间角色，例如 `small_table_1` 位于床边，功能上接近 `slot_nightstand_1`；也可能有多个同类实例，需要依靠关系约束区分谁对应哪个 slot。

因此，将 Slot–Instance Matching 正式定义为 **LoRAM（LoState Relation-Aware Matching）**。LoRAM 是 Dual-Track State Reviewer 内部的对齐模块，负责为 LoReview 提供可解释的问题归因，而不是作为独立的 graph matching 贡献。

#### 9.5.1 LoRAM 的输入与输出

输入：

```text
Goal LoState G
  - furniture_slots S = {s_i}
  - desired_relations E_G
  - required / optional flags
  - generation hints and avoid_refs

Observed LoState Ŝ
  - furniture_instances O = {o_j}
  - geometry: bbox / mask / centroid / area / orientation
  - measured_relations and hard geometry evidence
  - parser_confidence

Architecture JSON A
  - fixed anchors: walls, doors, windows, clearance regions
  - coordinate transform

semantic_registry_ref
  - category set
  - relation vocabulary

LoRAM dynamic candidate mining
  - exact candidates
  - dynamically discovered wrong-category candidates
  - incompatible pairs

optional previous Observed state
  - tracking consistency for editing / repair_round > 0
```

输出：

```text
slot_instance_alignment
unmatched_goal_slots
unmatched_observed_instances
wrong_category_candidates
relation_failures
relation_untestable
ambiguous_alignments
matching_evidence
```

这些输出不会直接执行修复，而是进入 LoReview，并进一步驱动 Qwen2.5-VL Planner 生成 RepairPlan 与 mask_spec。

#### 9.5.2 为什么不是简单类别计数

简单类别计数只能回答：

```text
Goal 需要几个 bed？
Observed 里有几个 bed？
```

但它不能回答：

```text
1. 同一类别多个实例时，哪个 instance 对应哪个 slot？
2. 一个 small_table 在床边时，它是 extra object，还是错误类别的 nightstand？
3. chair 不在 desk 附近时，它是目标 chair 位置错了，还是多余 chair？
4. relation violation 应该转成 MOVE、REPLACE，还是 INSERT？
```

LoRAM 的价值不是“匹配本身”，而是防止错误归因。例如：

```text
Goal: slot_nightstand_1 adjacent_to slot_bed_1
Observed: small_table_1 adjacent_to bed_1
```

类别计数可能输出：

```text
nightstand missing + small_table extra
```

LoRAM 应输出：

```text
slot_nightstand_1 ↔ small_table_1
issue = category_mismatch
suggested_action = REPLACE
```

这可以避免把一个局部 `REPLACE` 错误地变成 `DELETE + INSERT`。

#### 9.5.3 Partial Fused Matching 目标函数

LoRAM 将 Goal–Observed 对齐形式化为一个 **partial fused relation-aware matching** 问题。给定 Goal slots `S={s_i}` 与 Observed instances `O={o_j}`，引入带 dummy row / column 的 assignment matrix：

```text
X ∈ {0,1}^{(|S|+1) × (|O|+1)}
```

其中：

```text
X_ij = 1      表示 slot s_i 匹配到 instance o_j
X_i∅ = 1      表示 required / optional slot s_i 未匹配，即 missing
X_∅j = 1      表示 observed instance o_j 未匹配，即 extra
```

LoRAM 的目标函数为：

```text
E(X)
= (1 - α) · Ẽ_feature(X)
+ α · Ẽ_structure(X)
+ E_penalty(X)
```

其中 feature 项为：

```text
Ẽ_feature(X)
= 1 / |S| · Σ_{i∈S, j∈O} X_ij · D^F_ij
```

```text
D^F_ij
= λ_cat · C_cat(s_i, o_j)
+ λ_anchor · C_anchor(s_i, o_j; A)
+ λ_size · C_size(s_i, o_j)
+ λ_track · C_track(s_i, o_j)
```

structure 项为：

```text
Ẽ_structure(X)
= 1 / max(|E_G|, 1) ·
  Σ_{(s_i,p,s_k)∈E_G} Σ_{j∈O,l∈O}
  X_ij · X_kl · D^R_{ik,jl}(p)
```

penalty 项为：

```text
E_penalty(X)
= Σ_{i∈S} X_i∅ · μ_miss(s_i)
+ Σ_{j∈O} X_∅j · μ_extra(o_j)
```

约束为：

```text
Σ_j X_ij ≤ 1
Σ_i X_ij ≤ 1
X_ij ∈ {0,1}
```

`μ_miss` 与 `μ_extra` 的推荐设置原则：

```text
μ_miss(required slot) = M_miss
μ_miss(optional slot) = m_miss
μ_extra(instance)     = M_extra or category-dependent extra_cost
```

其中：

```text
M_miss  应显著大于任意正常 wrong-category match 的总代价；
m_miss  应明显小于 M_miss，用于 optional slot；
M_extra 应足以惩罚明显多余家具，但不应高到强迫系统把不兼容 instance 硬匹配给某个 slot。
```

推荐比例关系：

```text
M_miss(required)
> max(D^F candidate cost) + max(D^R relation cost)
```

这样可以保证：对于 required slot，系统会优先选择“有合理证据的 wrong-category candidate”，而不是过早把目标家具判为 missing；但如果所有候选都被 semantic gating 判为 incompatible，则仍然允许 `slot → dummy`，并在 LoReview 中生成 `entity_missing`。

同时：

```text
m_miss(optional) << M_miss(required)
```

因为 optional furniture 缺失不应与 required furniture 缺失同等严重。

`μ_extra` 可按 instance 风险调整：

```text
large furniture / blocks clearance / collides       → higher μ_extra
small optional accessory / low-risk decoration      → lower μ_extra
protected non-target                                → handled mainly by preservation checks, not by extra penalty
```

这里 `α` 控制 feature compatibility 与 relation consistency 的相对权重。由于 `Ẽ_feature` 和 `Ẽ_structure` 都经过 cardinality normalization，`α` 在不同房间规模下具有稳定含义。默认可在验证集上选择，例如 `α=0.4`，但不作为理论固定值。

#### 9.5.4 Feature Term：类别、锚点、尺寸与追踪

`D^F_ij` 描述单个 slot–instance pair 的局部兼容性。

**类别兼容性 `C_cat`** 不依赖预定义的 `functional_compatible` 替代表，也不依赖独立的 `category_prior_registry`。更合理的做法是：`semantic_registry_ref` 只提供稳定类别词表与 relation vocabulary；LoRAM 在回读 Observed LoState 后，根据当前实例的空间、尺寸、关系和语义证据，动态判断某个非 exact category instance 是否可以作为 wrong-category candidate。

因此，候选生成分三类：

```text
1. exact candidate:
   category(slot_i) == category(instance_j)

2. wrong-category candidate:
   category 不一致，
   但空间角色、尺寸先验、relation evidence 和 VLM 语义判断共同支持它可能承担目标 slot 的角色

3. incompatible:
   类别语义、形状或 hard constraint 明显冲突，即使局部关系满足，也不应匹配
```

例如：

```text
slot_nightstand_1:
  category = nightstand
  desired relation = adjacent_to bed

small_table_1:
  category = small_table
  observed relation = adjacent_to bed_1
  area = small
```

此时 LoRAM 可以根据当前证据动态生成：

```text
slot_nightstand_1 ↔ small_table_1
match_type = wrong-category candidate
```

但如果 `small_table_1` 出现在房间中央、远离 bed，或面积明显过大，则它不会进入候选池，而会更可能被判为 `entity_extra`。

再例如：

```text
slot_nightstand_1 ↔ chair_1
```

即使 `chair_1` 也在床边，关系上满足 `adjacent_to bed`，它仍然通常不应作为 nightstand 候选。原因是：关系证据可以支持 wrong-category candidate，但不能单独推翻类别语义边界。此时更合理的结果是：

```text
slot_nightstand_1 → dummy  => entity_missing
chair_1 → dummy            => entity_extra
```

推荐代价直觉：

```text
exact category match                                  → low cost, e.g. 0.0
wrong-category candidate with strong evidence         → medium cost
category mismatch with weak evidence                  → high cost
semantic / shape / hard-constraint conflict           → M
```

其中 `M` 是大数，用于 candidate gating。注意，语义边界与 hard constraint 的优先级高于 relation cost，避免出现为了满足关系而把 `bed`、`chair`、`wardrobe` 等明显不合适的实例强行匹配到 nightstand slot 的情况。

因此，`C_cat` 更准确地说不是“查一张替代表”，而是：

```text
C_cat(slot_i, instance_j)
= category exactness
+ penalty for semantic / shape conflict
- support from dynamic spatial-relation evidence
- support from VLM semantic review when ambiguous
```

通俗理解：

```text
类别完全一样                         → 很像，扣分低；
类别不一样但空间、尺寸、关系证据强     → 可以考虑，扣中等分；
类别不一样且语义或形状明显冲突         → 不该考虑，扣高分或禁止。
```

**建筑锚点一致性 `C_anchor`** 使用 Architecture JSON 中的固定参照物，不引入新的匹配变量：

```text
near arch:window_001              → normalized distance to window
avoid arch:door_001_clearance     → overlap ratio with clearance region
against wall                      → distance to nearest valid wall segment
```

Architecture anchors 是固定空间参照，而不是待匹配节点。它们只为 slot–instance matching 提供 anchor-consistency cost。

**尺寸先验 `C_size`** 用于判断 observed instance 的面积、长宽比是否符合目标 slot 的局部需求。例如，`small_table` 位于床边且面积适合作为床边小家具时，可以作为 `nightstand` 的 wrong-category candidate；大型 dining table 即使在床边，也不应匹配 nightstand。

**追踪一致性 `C_track`** 用于编辑与多轮修复：

```text
repair_round = 0      → 可忽略或低权重
repair_round > 0      → 优先延续 previous assignment / tracking_id
protected non-target  → 若被重新分配，代价升高
```

`C_track` 的直觉是：多轮修复时 LoRAM 不能每一轮都“失忆”。上一轮已经稳定确认的 slot–instance 对应，如果该对象没有落入本轮编辑 mask，也没有明显漂移，就应尽量保持原对应关系。

例如 round 0：

```text
slot_desk_1 ↔ desk_1
desk_1.tracking_id = track_desk_A
```

本轮修复目标是：

```text
REPLACE small_table_1 → nightstand
```

修复 mask 只覆盖 `small_table_1`。round 1 重新观察后，parser 可能重新命名实例：

```text
desk_2.tracking_id = track_desk_A
nightstand_1.tracking_id = track_table_B
```

此时 LoRAM 应保持：

```text
slot_desk_1 ↔ desk_2
```

而不是因为 instance_id 改变或类别轻微波动，把 `desk_2` 误判为 extra 或重新分配给其他 slot。可设计：

```text
C_track(slot_desk_1, desk_2) = 0.0
C_track(slot_desk_1, nightstand_1) = high
```

但 `C_track` 不能过强。如果对象位于本轮编辑 mask 内，且 action_type 是 REPLACE / MOVE / DELETE / INSERT，则 tracking 应根据 RepairPlan 的目标语义调整：

```text
target object inside edit mask:
  tracking 可用于确认修复轨迹延续，但不阻止类别改变；

protected non-target outside edit mask:
  tracking 应较强，防止非目标对象被重新解释；

newly inserted object:
  创建新的 tracking_id；

deleted target:
  tracking 终止。
```

因此，`C_track` 不是让系统固执，而是让闭环修复拥有跨 repair_round 的对象身份记忆。


#### 9.5.5 Structure Term：只检查 Goal desired relations

LoRAM 的 structure 项只对 Goal LoState 中显式存在的 desired relations `E_G` 计算，不构造 dense all-pair relation graph。

```text
Goal relation: e = (s_i, p, s_k)
Current assignment: s_i → o_j, s_k → o_l
Check: whether observed pair (o_j, o_l) satisfies predicate p
```

例如：

```text
slot_nightstand_1 adjacent_to slot_bed_1
```

若当前匹配为：

```text
slot_nightstand_1 → small_table_1
slot_bed_1 → bed_1
```

则检查：

```text
adjacent_to(small_table_1, bed_1)
```

`D^R` 按 relation necessity 区分 hard / soft cost：

```text
if necessity == required:
    D^R = hard_violation_cost

if necessity == preferred:
    D^R = soft_violation_cost
```

推荐：

```text
hard_violation_cost = 0            if satisfied
                    = M_hard       if violated

soft_violation_cost = β · violation²
```

其中 `M_hard` 应为大但有限的值，不能覆盖 semantic gating 的基本类别边界。

#### 9.5.6 Endpoint Unmatched：不惩罚已匹配对象

当 desired relation 的另一端 slot 未匹配时，LoRAM 不应给已匹配端点增加 relation penalty。

例如：

```text
Goal:
  bed required
  nightstand required
  nightstand adjacent_to bed required

Observed:
  bed_1 exists
  nightstand missing
```

此时 `nightstand adjacent_to bed` 无法验证，真正的问题是 nightstand 缺失，而不是 bed 匹配错误。因此：

```text
endpoint unmatched:
  C_rel 不增加惩罚
  relation 标记为 relation_untestable
  unmatched endpoint 生成 entity_missing
```

这避免将缺失对象导致的不可验证关系错误归因给已正确匹配的对象。

#### 9.5.7 求解：Iterative Hungarian Refinement

完整目标函数含有二次结构项，属于 QAP-like matching objective。对于本文的小规模室内布局审查，不需要重型 QAP / FGW solver。LoRAM 使用迭代 Hungarian 线性化近似求解。

算法：

```text
Input:
  D^F with dummy nodes
  Goal relation set E_G
  Observed measured relations E_O
  max iteration K
  α

Phase I: Initial assignment
  π⁰ = Hungarian(D^F)

Phase II: Iterative relation refinement
  for k = 0 ... K-1:
      for each candidate pair (s_i, o_j):
          compute normalized relation-induced cost C̄_rel^k(i,j)
          using testable desired relations involving s_i
          while other slots follow πᵏ

      C_eff^k(i,j)
      = (1 - α) · D^F_ij
      + α · C̄_rel^k(i,j)

      πᵏ⁺¹ = Hungarian(C_eff^k)

      if E(πᵏ⁺¹) > E(πᵏ):
          return πᵏ          // non-degradation safeguard

      if πᵏ⁺¹ == πᵏ:
          break

return π*
```

`C̄_rel^k(i,j)` 是局部线性化代价。计算时，系统暂时假设 `s_i → o_j`，其他 slots 保持当前匹配 `πᵏ`。这个 temporary assignment 只用于估计 relation-induced cost，可能与当前匹配冲突；随后的 Hungarian step 会重新保证一对一约束。

若 `s_i` 涉及的 desired relation 另一端未匹配，则该 relation 不进入 `C̄_rel^k` 的平均。若没有任何 testable relation，则：

```text
C̄_rel^k(i,j) = 0
```

建议：

```text
K = 2 或 3
```

因为典型室内房间对象数量较小，Goal relation graph 稀疏。

#### 9.5.8 Consistency Verification 与 VLM Ambiguity Review

最终匹配 `π*` 需要做 relation-by-relation verification，输出：

```text
consistent
violated_required
violated_preferred
marginal
untestable
```

触发 VLM review 的情况包括：

```text
Type A: low-margin assignment ambiguity
  top-1 / top-2 assignment cost gap < δ_amb

Type B: category–relation conflict
  类别证据弱，但空间关系强；或类别强，但关系显著失败

Type C: parser confidence affects required / hard / protected evidence
  触发 REOBSERVE，不交给 VLM 猜测

Type D: same-category ambiguity
  多个同类 instance 与多个同类 slot 的总代价接近，程序难以区分
```

Qwen2.5-VL 只处理 Type A / B / D 的语义歧义，例如判断 `small_table_1` 是否在功能上可视作 `nightstand` 的错误类别实例。若 parser uncertainty 影响 required slot、hard constraint 或 protected instance，则进入 `REOBSERVE`，而不是让 VLM 主观猜测。

#### 9.5.9 LoRAM → LoReview → RepairPlan 映射

LoRAM 的输出直接决定 LoReview issue 类型，并影响 Planner 生成的 RepairPlan：

| LoRAM 结果 | LoReview issue | Planner action |
|---|---|---|
| required slot → dummy | `entity_missing` | `INSERT` |
| optional slot → dummy | `optional_entity_missing` | optional `INSERT` / ignore |
| instance → dummy | `entity_extra` | `DELETE` |
| exact match + all relations consistent | no issue | no action |
| wrong-category candidate | `category_mismatch` | `REPLACE` |
| required relation violated | `relation_issue` | `MOVE` / `ADJUST` |
| preferred relation violated | `soft_relation_issue` | lower-priority `MOVE` |
| clearance overlap | `hard_geometry_issue` | `MOVE` / `ADJUST` |
| relation endpoint unmatched | `relation_untestable + entity_missing` | `INSERT` missing endpoint first |
| low-margin assignment | `ambiguous_alignment` | VLM review |
| same-category undifferentiable | `same_category_ambiguity` | VLM review |
| parser confidence affects hard evidence | `observation_issue` | `REOBSERVE` |

这一映射是 LoRAM 的核心价值。LoRAM 不是为了提升平均匹配分数，而是为了减少错误归因导致的不必要编辑。例如，本应执行 `REPLACE small_table_1 → nightstand` 的问题，不应误判为 `DELETE small_table_1 + INSERT nightstand`。

#### 9.5.10 LoRAM 示例

```json
{
  "matching_method": "LoRAM",
  "repair_round": 0,
  "slot_instance_alignment": [
    {
      "slot_id": "slot_bed_1",
      "instance_id": "bed_1",
      "match_type": "exact",
      "confidence": 0.96,
      "evidence": [
        "exact category match",
        "size prior within range",
        "anchor hints satisfied"
      ],
      "relation_scores": {
        "dr_nightstand_bed": "untestable_due_to_missing_endpoint"
      }
    },
    {
      "slot_id": "slot_nightstand_1",
      "instance_id": "small_table_1",
      "match_type": "wrong_category_candidate",
      "confidence": 0.72,
      "evidence": [
        "small_table is functionally compatible with nightstand only under bedside context",
        "small_table_1 adjacent_to bed_1",
        "area within bedside-furniture prior"
      ],
      "flagged_issue": {
        "type": "category_mismatch",
        "suggested_action_type": "REPLACE"
      }
    }
  ],
  "unmatched_goal_slots": [],
  "unmatched_observed_instances": [
    {
      "instance_id": "chair_1",
      "reason": "no compatible required slot and no supporting desired relation",
      "suggested_action_type": "DELETE"
    }
  ],
  "ambiguous_alignments": []
}
```

#### 9.5.11 评估与消融

LoRAM 的评估重点不只是 alignment accuracy，而是 **issue attribution accuracy** 与 **unnecessary edit rate**。因为在多数简单房间中，category + anchor matching 已经足够；LoRAM 的真正价值是避免少数情况下的灾难性误归因。

消融：

| 方法 | 描述 |
|---|---|
| CatCount | 只按类别数量判断 |
| CatHungarian | 只用 category cost 做一对一匹配 |
| LoRAM-α=0 | feature term only，不使用 structure term |
| LoRAM-noDummy | 不显式建模 missing / extra |
| LoRAM-noVLM | 不使用 VLM ambiguity review |
| LoRAM-Full | 完整 LoRAM |

关键指标：

```text
alignment accuracy
issue attribution accuracy
catastrophic misattribution rate
unnecessary edit rate
wrong action type rate
downstream repair correctness
average repair_round
rollback rate
```

其中：

```text
catastrophic misattribution rate
```

用于衡量是否把 `category_mismatch` 错判为 `missing + extra`，或把 `relation_issue` 错判为 `entity_missing` 等高代价错误。


### 9.6 LoReview 示例

```json
{
  "schema_version": "loreview-v1.4",
  "task_id": "bedroom_case_001",
  "review_id": "review_round0",
  "goal_ref": "goal_bedroom_case_001",
  "observed_ref": "obs_bedroom_case_001_round0",
  "repair_round": 0,
  "track_a_geometry_review": [
    {
      "issue_id": "issue_missing_nightstand_001",
      "type": "entity_missing",
      "severity": "error",
      "related_goal_refs": ["slot_nightstand_1"],
      "related_observed_refs": [],
      "description": "Required nightstand slot is not matched by any observed instance."
    }
  ],
  "track_b_semantic_review": [
    {
      "issue_id": "issue_accessibility_001",
      "type": "soft_semantic_issue",
      "severity": "warning",
      "related_refs": ["bed_1", "arch:door_001_clearance"],
      "description": "The circulation near the bed is semantically narrow and should be kept clear.",
      "confidence": 0.74
    }
  ],
  "recommended_next_step": "PLAN_REPAIR"
}
```

---

## 10. Violation Ranking：先修什么

Violation Ranking 不属于 LoState 本体，但它决定 Correction Planner 的输入顺序。

### 10.1 排序原则

```text
1. 硬约束优先；
2. required relation 优先于 preferred relation；
3. 局部可修复问题优先；
4. preservation risk 低的问题优先；
5. uncertainty 高的问题先 REOBSERVE，而不是 destructive edit。
```

### 10.2 推荐 scoring

```text
score(v)
= w₁ * severity
+ w₂ * locality
+ w₃ * fixability
- w₄ * preservation_risk
- w₅ * estimated_edit_cost
- w₆ * observation_uncertainty
```

这里使用 `w₁, w₂, ...`，避免与 LoRAM 目标函数中的 `α` 混淆。Violation Ranking 的权重只用于决定“先修哪个 violation”；LoRAM 的 `α` 用于控制 slot–instance matching 中 feature term 与 structure term 的相对重要性。二者不是同一组参数。

Ranking 只决定“先把哪个 violation 交给 Planner”；mask 的区域仍由 Qwen2.5-VL Planner 通过 `mask_spec` 决定。

---

## 11. RepairPlan：VLM 修正计划与 mask_spec

RepairPlan 不属于 LoState 本体。它是 Qwen2.5-VL Correction Planner 的结构化输出。

### 11.1 RepairPlan 设计原则

RepairPlan 不是最终 `control_mask`，也不是自由文本编辑命令，而是结构化动作规格。它应该回答：

```text
1. 改什么？
2. 为什么改？
3. VLM 认为应该编辑哪个区域？
4. mask_spec 用哪种表达形式？
5. 哪些对象和建筑区域应被保护？
6. 喂给 Qwen-Image-ControlNet-Inpainting 的 descriptive prompt 是什么？
7. 如何验收？
```

### 11.2 动作类型最小集

| action_type | 使用场景 | 推荐 mask_spec |
|---|---|---|
| INSERT | 缺失家具 | `bbox` / `polygon`，表示允许生成区域，不是家具最终轮廓 |
| DELETE | 多余家具 | `instance_ref`，由 VLM 指定要删除的 observed instance |
| MOVE | 位置/关系违规 | `old_new_union`，旧位置清除 + 新位置生成 |
| REPLACE | 类别错误或功能不符 | `instance_ref` 或 `bbox` |
| ADJUST_ORIENTATION | 朝向错误 | `instance_ref` 或 `bbox`，覆盖完整目标家具与局部上下文 |
| REOBSERVE | 观测不确定，不宜直接编辑 | 不触发 inpainting |

### 11.3 mask_spec 类型

固定支持以下 `mask_spec.mask_type`：

```text
1. instance_ref
2. bbox
3. polygon
4. old_new_union
5. full_regenerate
```

#### `instance_ref`

适合 DELETE / REPLACE / ADJUST_ORIENTATION：

```json
{
  "mask_type": "instance_ref",
  "instance_refs": ["chair_1"],
  "context_margin_px": 12
}
```

#### `bbox`

适合规则矩形区域：

```json
{
  "mask_type": "bbox",
  "coordinate_space": "image_pixel",
  "image_size_px": [1024, 1024],
  "bbox_px": [180, 330, 305, 510],
  "context_margin_px": 8
}
```

#### `polygon`

适合不规则局部区域：

```json
{
  "mask_type": "polygon",
  "coordinate_space": "image_pixel",
  "image_size_px": [1024, 1024],
  "polygon_px": [[180, 330], [305, 330], [305, 510], [180, 510]],
  "context_margin_px": 8
}
```

#### `old_new_union`

适合 MOVE：

```json
{
  "mask_type": "old_new_union",
  "old_instance_refs": ["desk_1"],
  "new_region": {
    "type": "bbox",
    "bbox_px": [620, 120, 820, 260]
  },
  "old_margin_px": 10,
  "new_margin_px": 14
}
```

#### `full_regenerate`

只作为连续局部修复失败后的 fallback：

```json
{
  "mask_type": "full_regenerate",
  "reason": "Local repair failed after K attempts."
}
```

### 11.4 RepairPlan 示例

```json
{
  "schema_version": "repair_plan-v1.4",
  "task_id": "bedroom_case_001",
  "repair_plan_id": "action_round0",
  "repair_round": 0,
  "actions": [
    {
      "repair_step_id": "act_insert_nightstand_001",
      "trigger_violation": "v_missing_nightstand_001",
      "action_type": "INSERT",
      "target_ref": {
        "target_kind": "furniture_slot",
        "slot_id": "slot_nightstand_1",
        "target_category": "nightstand"
      },
      "spatial_reasoning": {
        "target_relation": "adjacent_to bed_1",
        "avoid_refs": ["arch:door_001_clearance"],
        "why_this_region": "The selected region is beside bed_1, has enough free space for a nightstand, and does not overlap the door clearance."
      },
      "mask_spec": {
        "generated_by": "Qwen2.5-VL_CorrectionPlanner",
        "mask_type": "polygon",
        "coordinate_space": "image_pixel",
        "image_size_px": [1024, 1024],
        "polygon_px": [[180, 330], [305, 330], [305, 510], [180, 510]],
        "binary_value": {
          "edit_region": 255,
          "preserve_region": 0
        },
        "postprocess": {
          "dilate_px": 8,
          "min_area_px": 512,
          "max_area_ratio": 0.18
        }
      },
      "protected_refs": [
        "bed_1",
        "desk_1",
        "arch:door_001_clearance"
      ],
      "correction_prompt": "A top-down fixed-palette semantic bedroom layout. The masked region contains one nightstand placed beside the bed. The bed, desk, wardrobe, walls, door, window, and door clearance outside the masked region remain unchanged.",
      "negative_prompt": "Do not move existing furniture outside the masked region. Do not block the door clearance.",
      "acceptance_criteria": [
        "nightstand_count_match",
        "adjacent_to_bed",
        "no_collision",
        "no_clearance_overlap",
        "non_target_preservation"
      ],
      "confidence": 0.86
    }
  ]
}
```

### 11.5 Planner 可以与不可以输出什么

Planner 可以输出：

```text
action_type
target_ref
spatial_reasoning
mask_spec
protected_refs
correction_prompt
negative_prompt
acceptance_criteria
confidence
```

Planner 不应输出：

```text
1. 直接喂给 Qwen-Image-ControlNet-Inpainting 的 raw tensor；
2. 覆盖 Observed LoState 几何真值的新 bbox / mask；
3. 不存在的 architecture anchor；
4. 未在 ontology 中注册的家具类别；
5. 与 image_size_px 不一致的坐标。
```

---

## 12. Spatial Context Provider：给 VLM 的空间上下文，而不是替 VLM 决定 mask

v1.4.7 不再使用较抽象的 `runtime masks / geometry summaries` 表述，统一改为：

```text
runtime spatial evidence
```

它表示：**当前 repair_round 中由程序临时计算出来、用于辅助 VLM Planner 理解空间的证据包**。它不是 LoState 本体，也不是最终喂给 Qwen-Image-ControlNet-Inpainting 的 `control_mask`。

换言之：

```text
runtime spatial evidence = 给 VLM 看的空间证据；
mask_spec    = VLM 在 RepairPlan 中确认的编辑区域规格；
control_mask             = Mask Tensor Adapter 栅格化后的最终二值 mask。
```

### 12.1 输入

```text
Observed LoState
+ Architecture JSON
+ LoReview
+ runtime spatial evidence
```

其中 `runtime spatial evidence` 可以由 Programmatic State Observer、Reviewer 或 Spatial Context Provider 在当前轮次临时计算得到，包括：

```text
1. object instance masks；
2. free-floor mask；
3. clearance / door-swing masks；
4. collision masks；
5. protected-object mask；
6. bbox / centroid / area / orientation summaries；
7. distance / overlap / anchor-relation measurements；
8. optional available-region hints。
```

这些信息都来自当前的 Observed LoState、Architecture JSON 与 runtime geometry computation。它们可以被缓存到 runtime cache 中，但不应写回 LoState canonical JSON 作为状态本体。

### 12.2 runtime spatial evidence 的具体含义

#### object instance masks

由 Observed LoState 中的家具实例 mask 得到，例如：

```text
bed_1 mask
desk_1 mask
chair_1 mask
wardrobe_1 mask
```

用途：

```text
1. 帮助 VLM 理解每个 observed instance 的真实占据区域；
2. 当 action_type = DELETE / REPLACE / ADJUST_ORIENTATION 时，支持 Planner 输出 instance_ref；
3. Adapter 后续可根据 instance_ref 解码对应 mask，生成 control_mask。
```

注意：object instance mask 是“观测到的对象区域”，不是最终编辑 mask。

#### free-floor mask

表示当前房间中未被墙体、家具、clearance 等占据的可用空地。

用途：

```text
1. 帮助 VLM 判断 INSERT 是否有可用空间；
2. 辅助判断某个新家具是否可能放入目标区域；
3. 作为 available-region hint 提供给 VLM。
```

free-floor mask 不能直接替代 VLM 的 mask planning。它只能告诉 VLM “哪里可能可用”，最终编辑区域仍由 VLM 通过 `mask_spec` / `mask_spec` 明确给出。

#### clearance / door-swing masks

表示门口 clearance、开门轨迹或通行区域。

用途：

```text
1. 帮助 VLM 避免把新家具规划到门口区域；
2. 支持 Reviewer 判断 no_clearance_overlap；
3. 支持 AcceptanceController 检查修复后是否引入新 hard violation。
```

#### collision masks

当两个家具发生重叠或碰撞时，可以计算：

```text
collision_mask = mask(object_a) ∩ mask(object_b)
```

用途：

```text
1. 告诉 VLM 碰撞发生在哪个局部区域；
2. 辅助 Planner 判断是 MOVE、DELETE、ADJUST，还是需要 REOBSERVE；
3. 辅助 AcceptanceController 检查 primary_violation 是否改善。
```

#### protected-object mask

表示当前修复中不应被改变的对象区域，例如：

```text
protected_object_mask = bed_1 ∪ desk_1 ∪ wardrobe_1
```

用途：

```text
1. 帮助 VLM 避免把 mask_spec 画到 protected object 上；
2. 支持 prompt 中的 “outside masked region remains unchanged”；
3. 支持 AcceptanceController 做 non-target preservation 检查。
```

#### geometry summaries

geometry summaries 是数字化的空间摘要，而不是 mask 图像。例如：

```json
{
  "object_summaries": [
    {
      "instance_id": "bed_1",
      "category": "bed",
      "bbox_px": [120, 260, 420, 620],
      "centroid_px": [270, 440],
      "area_px": 82000
    }
  ],
  "relation_measurements": [
    {
      "predicate": "adjacent_to",
      "subject": "small_table_1",
      "object": "bed_1",
      "distance_px": 12,
      "satisfied": true
    }
  ],
  "clearance_overlaps": [
    {
      "instance_id": "desk_1",
      "clearance_ref": "arch:door_001_clearance",
      "overlap_ratio": 0.18
    }
  ]
}
```

用途：

```text
1. 让 VLM 不只“看图”，还读取精确几何证据；
2. 减少 VLM 对距离、面积、overlap 的主观猜测；
3. 帮助 VLM 输出更可靠的 mask_spec。
```

#### optional available-region hints

系统可以根据 free-floor mask、目标 slot 的 relation 需求和 clearance 约束，给出候选空地摘要。例如：

```json
"context_candidates": [
  {
    "region_id": "free_region_bed_right_001",
    "bbox_px": [180, 330, 305, 510],
    "near": "bed_1",
    "overlap_clearance": 0.0,
    "estimated_fit": "nightstand"
  }
]
```

但这只是上下文提示，不是最终区域决策。VLM Planner 必须在 RepairPlan 中明确确认或改写编辑区域。

### 12.3 输出给 VLM 的上下文

Spatial Context Provider 给 VLM 的上下文可以包括：

```text
1. object bbox / mask summary；
2. free-floor summary；
3. clearance regions；
4. collision pairs；
5. anchor distances；
6. relation measurements；
7. protected-object summary；
8. optional available-region hints。
```

这些内容可以以结构化 JSON、可视化 overlay 或文字摘要的形式提供给 Qwen2.5-VL Planner。论文主文只需强调其功能，不必固定唯一实现格式。

### 12.4 设计原则

```text
1. Spatial Context Provider 可以帮助 VLM 理解空间，但不替 VLM 选择最终编辑区域；
2. runtime spatial evidence 是上下文证据，不是 control_mask；
3. optional available-region hints 只是候选提示，不是程序层区域决策；
4. 最终编辑区域必须由 Qwen2.5-VL Planner 在 RepairPlan 中通过 mask_spec 显式给出；
5. Mask Tensor Adapter 只负责把 VLM 确认后的 mask_spec 转成 binary control_mask。
```

如果系统自动提供候选区域，也只能作为 `context_candidates` 输入给 VLM；VLM 仍需在 RepairPlan 中确认或改写 mask_spec。

### 12.5 与 control_mask 的边界

必须明确：

```text
runtime spatial evidence ≠ control_mask
```

对比：

| 名称 | 含义 | 是否喂给 Qwen-Image-ControlNet-Inpainting |
|---|---|---|
| runtime spatial evidence | 给 VLM 的空间证据包 | 否 |
| mask_spec | VLM 输出的编辑区域规格 | 否，需先适配 |
| control_mask | Adapter 生成的二值 mask | 是 |

因此，Spatial Context Provider 不应输出最终 `control_mask`，也不应绕过 VLM Planner 直接决定修复区域。


---

## 13. Mask Tensor Adapter：从 VLM mask_spec 到 binary control_mask

### 13.1 为什么需要 Adapter

InstantX/Qwen-Image-ControlNet-Inpainting 的推理接口使用：

```text
control_image + control_mask + prompt
```

其中 `control_mask` 是图像/张量形式，不是 JSON。Qwen2.5-VL Planner 输出的是结构化 `mask_spec`，因此需要一个 Adapter 将其变成 pipeline 可用的二值灰度 mask。

### 13.2 Adapter 输入输出

输入：

```text
RepairPlan.mask_spec
+ Observed LoState geometry masks
+ image_size_px
```

输出：

```text
control_mask: uint8[H, W]
  255 = edit / inpaint region
  0   = preserve region
```

### 13.3 Adapter 允许做什么

```text
1. decode instance_ref 对应的 Observed object mask；
2. rasterize bbox / polygon；
3. union old and new masks for MOVE；
4. apply binary dilation / erosion；
5. resize / align to control_image size；
6. ensure H,W divisible by 16 when required by execution pipeline；
7. binarize to {0,255}；
8. validate min_area / max_area_ratio；
9. export control_mask.png / mask tensor；
10. record mask metadata for revision log。
```

### 13.4 Adapter 不应该做什么

```text
1. 自己决定修哪个 violation；
2. 自己选择语义编辑区域；
3. 自动换成另一个候选区域；
4. 修改 VLM 的 target_ref；
5. 改写 Observed LoState 的几何事实；
6. 在 mask_spec 非法时悄悄替 VLM 重规划。
```

如果 `mask_spec` 非法，Adapter 应返回：

```text
INVALID_MASK_PLAN
```

然后触发 Planner revise，而不是由程序擅自改变语义区域。

### 13.5 binary mask 规范

由于 InstantX pipeline 的 mask processor 会将 mask 转为灰度并二值化，v1.4 默认采用二值 mask：

```text
control_mask format:
  single-channel grayscale PNG / PIL image / uint8 tensor
  size: same as control_image
  edit region: 255 / white
  preserve region: 0 / black
```

默认不使用 soft feather 作为主设计。若未来修改 pipeline 的 mask processor，使其保留 soft mask，则可作为扩展实验。

---

## 14. Qwen-Image-ControlNet-Inpainting 执行接口

### 14.1 固定执行器

固定使用：

```text
Qwen-Image-ControlNet-Inpainting
```

作为局部修复执行器。本文不再写成 executor-agnostic，因为训练与推理都需要固定 mask 格式、prompt 格式和输入输出契约。

### 14.2 标准推理输入

```text
control_image: current semantic layout image Iᵗ
control_mask: binary mask Mᵗ
prompt: descriptive final-state correction prompt
negative_prompt: optional preservation / avoidance prompt
controlnet_conditioning_scale: default 1.0
width / height: same as control_image and control_mask
```

### 14.3 prompt 设计

InstantX 模型卡建议使用详细描述整个图像的 descriptive prompt，而不是 instructive prompt。因此 `correction_prompt` 应描述修复后的目标状态，而不是直接命令模型执行操作。

不推荐：

```text
Delete the extra chair.
Move the desk to the window.
Fix the collision.
```

推荐：

```text
A top-down fixed-palette semantic bedroom layout. The masked region contains one desk placed near the window. The bed, wardrobe, nightstand, walls, door, window, and door clearance outside the masked region remain unchanged.
```

### 14.4 不同 action_type 的 prompt 和 mask 约定

| action_type | mask_spec | prompt 应描述 |
|---|---|---|
| INSERT | bbox / polygon | masked region 中应出现的目标家具及其关系 |
| DELETE | instance_ref | masked region 应恢复为空地/可通行区域，其他对象不变 |
| MOVE | old_new_union | 最终状态中目标家具位于新位置，旧位置恢复为空地 |
| REPLACE | instance_ref / bbox | masked object 替换为目标类别 |
| ADJUST_ORIENTATION | instance_ref / bbox | 目标家具以期望朝向出现 |

---

## 15. LoRepair：LoState-guided Local Repair Loop

`LoRepair` 不是新的模型、状态 schema 或执行器，而是本文闭环局部修复流程的算法名称。它把以下组件串联成一个可验证的 repair loop：

```text
LoReview
→ Violation Ranking
→ Qwen2.5-VL Correction Planner
→ Mask Tensor Adapter
→ Qwen-Image-ControlNet-Inpainting
→ State Observer
→ State Reviewer
→ AcceptanceController
```

原先的 `LoRepair-SD` 容易让读者误解为 Stable Diffusion 相关模块，因此本文不再使用 `-SD` 后缀。其核心含义保留为：

```text
state-difference-guided local repair with VLM mask planning
```

也就是说，修复不是自由编辑，而是由 Goal LoState 与 Observed LoState 的差异驱动；每一轮只选择一个高优先级 violation，由 Qwen2.5-VL Planner 生成结构化修复动作与编辑区域规格，再交给 Qwen-Image-ControlNet-Inpainting 执行局部修复。

### 15.1 算法流程

```text
Input:
  User instruction U
  Architecture JSON A
  Goal LoState G
  Semantic layout image Iᵗ
  Observed LoState Ŝᵗ

Step 1: Review
  Rᵗ = StateReviewer(G, Ŝᵗ)

Step 2: Rank
  Vᵗ = RankViolations(Rᵗ)

Step 3: Plan repair
  pᵗ = Qwen2.5-VL_Planner(
      G,
      Ŝᵗ,
      Rᵗ,
      Iᵗ,
      top-ranked violation
  )

  where pᵗ contains:
      action_type
      target_ref
      mask_spec
      protected_refs
      correction_prompt
      acceptance_criteria

Step 4: Rasterize mask specification
  Mᵗ = MaskTensorAdapter(
      pᵗ.mask_spec,
      Ŝᵗ
  )

Step 5: Execute local repair
  Iᵗ⁺¹ = QwenImageControlNetInpainting(
      control_image = Iᵗ,
      control_mask  = Mᵗ,
      prompt        = pᵗ.correction_prompt
  )

Step 6: Re-observe
  Ŝᵗ⁺¹ = StateObserver(Iᵗ⁺¹, A)

Step 7: Re-verify
  Rᵗ⁺¹ = StateReviewer(G, Ŝᵗ⁺¹)

Step 8: Accept or rollback
  if Accept(Rᵗ, Rᵗ⁺¹, Ŝᵗ, Ŝᵗ⁺¹):
      keep Iᵗ⁺¹, Ŝᵗ⁺¹
  else:
      rollback to Iᵗ, Ŝᵗ
```

### 15.2 为什么这样设计

```text
1. LoRepair 只是闭环局部修复流程名，不是额外模型；
2. 修复由 LoReview 中的 state difference 驱动，而不是由自由文本随意编辑；
3. Violation Ranking 决定“先修哪个问题”；
4. Qwen2.5-VL Planner 决定“怎么修、修哪里、prompt 怎么写”；
5. 程序层不抢走 VLM 的 mask planning 职责；
6. VLM 不需要输出 raw tensor，只输出可监督、可解析的 mask_spec；
7. Mask Tensor Adapter 将 mask_spec 转成 Qwen-Image-ControlNet-Inpainting 需要的 binary control_mask；
8. 执行器固定为 Qwen-Image-ControlNet-Inpainting，对齐 control_image + control_mask + prompt 接口；
9. 修复后必须重新观察、重新审查，并由 AcceptanceController 决定 accept 或 rollback；
10. 训练时可以同时监督 Planner 的结构化修复计划和 Inpainting executor 的 mask-conditioned repair。
```

一句话：

```text
LoRepair = LoState / LoReview 驱动的闭环局部修复算法流程。
```

它不表示一个独立模块，而表示一轮修复如何从“发现问题”走到“规划、执行、再验证、接受或回滚”。

---

## 16. AcceptanceController：验收与回滚

### 16.1 输入输出

输入：

```text
old Observed LoState Ŝᵗ
new Observed LoState Ŝᵗ⁺¹
old LoReview Rᵗ
new LoReview Rᵗ⁺¹
RepairPlan aᵗ
control_mask Mᵗ
```

输出：

```text
accept / reject / rollback / reobserve / revise_mask_spec
```

### 16.2 接受准则

推荐冻结为：

```text
Accept(Iᵗ⁺¹) iff:
1. primary_violation_improved；
2. no_new_hard_violation；
3. non_target_preservation_above_threshold；
4. total_cost_lexicographically_decreases；
5. edited_area is compatible with Mᵗ within tolerance。
```

### 16.3 字典序 cost

```text
C_t = (
  #hard_violations,
  #required_relation_violations,
  #preservation_violations,
  #soft_violations,
  uncertainty_penalty
)
```

接受条件：

```text
C_{t+1} <_lex C_t
```

并且：

```text
new_hard_violations == 0
```

### 16.4 Mask-spec 失败处理

如果修复失败但原因是 mask_spec 不合理，系统应返回给 Planner：

```json
{
  "feedback_type": "MASK_PLAN_REVISION_REQUIRED",
  "failed_repair_step_id": "act_insert_nightstand_001",
  "reason": "Mask region too small to generate a complete nightstand.",
  "suggested_revision": "Expand the polygon region around the selected free floor area."
}
```

这保持 VLM 作为 planner 的地位：程序不擅自重选区域，而是要求 VLM revise。

---

## 17. 训练设计 

训练必须同时支持：

```text
1. Qwen2.5-VL Planner 学会输出 RepairPlan + mask_spec；
2. Qwen-Image-ControlNet-Inpainting 学会根据 binary control_mask + descriptive prompt 修复 semantic layout。
```

### 17.1 训练数据构造

```text
GT semantic layout I_gt
→ 扰动生成 I_bad
   missing / extra / misplaced / collision / wrong relation / wrong category / wrong orientation
→ State Observer 回读 I_bad → Observed LoState Ŝ_bad
→ StateReviewer(G, Ŝ_bad) → LoReview D
→ 自动计算 oracle edit region M*
→ 把 M* 压缩成 mask_spec 表达：
   instance_ref / bbox / polygon / old_new_union
```

### 17.2 Qwen2.5-VL Planner SFT

输入：

```text
I_bad
Goal LoState G
Observed LoState Ŝ_bad
LoReview D
Architecture / spatial context summary
```

监督输出：

```text
RepairPlan + mask_spec + correction_prompt
```

目标：让 VLM 在 LoState 约束下显式学习空间编辑区域规划。

### 17.3 Qwen-Image-ControlNet-Inpainting 领域适配

训练三元组：

```text
control_image = I_bad
control_mask  = rasterize(mask_spec)
prompt        = correction_prompt
target        = I_gt or locally repaired target
```

mask 分布不应只用完美 GT diff mask，而应混合：

```text
1. exact oracle mask；
2. bbox-converted oracle mask；
3. polygon-simplified oracle mask；
4. dilated binary oracle mask；
5. VLM predicted mask_spec rasterized mask。
```

原因：推理时 Planner 输出的 mask_spec 不会永远等于完美差分区域，executor 需要适应 VLM-style mask distribution。

### 17.4 MOVE 的训练特殊处理

MOVE 应训练为：

```text
old position clearing + new position insertion
```

mask_spec 使用：

```text
old_new_union
```

训练 target 应体现：

```text
旧位置恢复为空地；
新位置出现目标家具；
其他对象不变。
```

---

## 18. Runtime Cache Boundary

v1.4 采用三层工程结构：

```text
1. Canonical JSON State
   - Goal LoState
   - Observed LoState
   - LoReview
   - RepairPlan with mask_spec

2. Runtime Tensor Cache
   - label_map: uint8[H, W]
   - instance_map: int32[H, W]
   - free_floor_mask: bool[H, W]
   - object_mask: bool[H, W]
   - control_mask: uint8[H, W]

3. On-demand Relation / Spatial Context View
   - desired relation subset
   - hard-check relation subset
   - planner-needed spatial summary
```

`control_mask` 不进入 LoState 本体，但应在 Revision Log 中记录 `control_mask_id`。

---

## 19. JSON Schema 与工程文件清单

v1.4 建议冻结以下工程文件：

| 文件 | 作用 |
|---|---|
| `architecture.schema.json` | Architecture JSON 规范 |
| `lostate_goal.schema.json` | Goal LoState 规范 |
| `lostate_observed.schema.json` | Observed LoState 规范 |
| `loreview.schema.json` | LoReview 状态审查规范 |
| `repair_plan.schema.json` | RepairPlan + mask_spec 规范 |
| `mask_spec.schema.json` | VLM mask_spec 输出规范 |
| `mask_tensor_adapter.py` | mask_spec → binary control_mask 的工程适配 |
| `palette_registry.json` | 固定色板与类别映射 |
| `semantic_registry.json` | 类别、同义词、父子类、类别属性先验 |
| `relation_registry.json` | predicate 参数、单位与阈值 |
| `revision_log.jsonl` | 每轮修复、验收、回滚记录 |

### 19.1 校验要求

每个 JSON 输出必须满足：

```text
1. schema_version 可识别；
2. required fields 完整；
3. 所有 arch:* 引用可在 Architecture JSON 中解析；
4. 所有 category_id 可在 ontology / palette 中解析；
5. 所有 relation predicate 可在 relation_registry 中解析；
6. 所有 instance_id / slot_id / violation_id 引用可追踪；
7. mask_spec 坐标必须匹配 image_size_px；
8. control_mask 必须与 control_image 尺寸一致；
9. control_mask 必须是二值编辑区域；
10. Planner 不得输出 schema 外字段来绕过 Mask Tensor Adapter。
```

---

## 20. 与 Qwen2.5-VL / Qwen-Image-ControlNet-Inpainting 的接口边界

### 20.1 Qwen2.5-VL 的三角色

同一个 Qwen2.5-VL 权重承担三种状态相关角色：

```text
1. Target LoState Constructor
2. Track B Reviewer
3. Correction Planner with VLM Mask Planning
```

推荐 task tags：

```text
[TARGET_STATE_CONSTRUCTION]
[SOFT_VERIFICATION]
[CORRECTION_PLANNING_WITH_MASK_PLAN]
```

### 20.2 Qwen-Image-ControlNet-Inpainting 的角色

Qwen-Image-ControlNet-Inpainting 负责：

```text
1. 接收 current semantic layout image 作为 control_image；
2. 接收 binary control_mask；
3. 接收 descriptive final-state prompt；
4. 输出修复后的 semantic layout image。
```

Qwen-Image-ControlNet-Inpainting 不负责：

```text
1. LoState constructor；
2. LoReview reviewer；
3. correction planner；
4. mask_spec planner；
5. hard geometric verifier。
```

### 20.3 必须坚持的边界

```text
Qwen2.5-VL = understand / construct / verify softly / plan action + mask_spec
Qwen-Image-ControlNet-Inpainting = execute masked semantic layout repair
Program = measure / compare hard constraints / rasterize mask_spec / validate / accept or rollback
```

---

## 21. Evaluation Hooks

| 指标组 | 指标 | 来源字段 |
|---|---|---|
| 接口有效性 | JSON Validity / Executable Rate | schema validation |
| mask 规划 | Mask Plan Validity / Mask Area Ratio / Invalid Mask Rate | `mask_spec.schema.json` + Adapter log |
| 语义完整性 | Count Match | `furniture_slots` + `furniture_instances` + LoReview |
| 几何合规性 | Collision-Free / Boundary Pass / Clearance Pass | `hard_constraint_evidence` |
| 关系合理性 | Relation Satisfaction | `desired_relations` + `measured_relations` + LoReview |
| 编辑保持性 | Non-target Mask IoU / Center Shift / Category Consistency | `tracking_id` + previous Observed |
| 修复效率 | One-step Acceptance / Final Pass Rate / Avg. Iterations | `revision_log.jsonl` |
| executor 适配 | Inpaint Success Rate / Rollback Rate | repair log + acceptance decision |

### 21.1 mask 相关消融

| 方法 | 说明 | 目的 |
|---|---|---|
| Programmatic-only mask | 不让 VLM 输出 mask_spec，直接由规则构造 mask | 验证 VLM mask planning 的必要性 |
| VLM bbox-only | Planner 只能输出 bbox | 验证 polygon / instance_ref / old_new_union 的价值 |
| VLM full mask_spec | Planner 输出完整 mask_spec 类型集合 | 主方法 |
| Oracle mask | 从 GT 差分获得理想 mask | 上界 |

---

## 22. 采纳与不采纳记录

### 22.1 v1.4 已采纳设计点

| 设计点 | 采纳位置 |
|---|---|
| 固定 Qwen-Image-ControlNet-Inpainting 执行器 | 第 14 节 |
| Qwen2.5-VL 始终输出 mask_spec | 第 11 节 |
| 程序层改为 Mask Tensor Adapter | 第 13 节 |
| binary control_mask 规范 | 第 13 节 |
| descriptive final-state prompt | 第 14 节 |
| MOVE = old_new_union | 第 11 / 17 节 |
| Planner SFT 学 RepairPlan + mask_spec | 第 17 节 |
| Inpainting executor 学 image + binary mask + prompt → target | 第 17 节 |
| Spatial Context Provider 辅助 VLM，而不替 VLM 选区域 | 第 12 节 |

### 22.2 保留但弱化的设计点

| 设计点 | 处理方式 |
|---|---|
| CandidateRegionGenerator | 不作为主决策器，仅作为可选 spatial context / ablation |
| Programmatic mask construction | 不作为主方法，只作为 programmatic-only baseline |
| LoRepair-GC / 图一致性传播 | future extension / optional ablation |
| dense relation graph | 不进入主 schema，只允许 on-demand view |

### 22.3 明确不采纳的旧表述

| 旧表述 | 不采纳原因 |
|---|---|
| “Mask 由程序构造，不由 VLM 输出” | 与 VLM 空间语义规划主张冲突 |
| “Planner 不可以输出 bbox / mask” | v1.4 中 Planner 必须输出结构化 bbox / polygon / instance_ref / old_new_union mask_spec |
| “Programmatic MaskBuilder 是主修复模块” | v1.4 改为 Mask Tensor Adapter，职责是格式适配而非语义决策 |
| “control_mask 可默认 soft/feather” | InstantX pipeline 会二值化 mask，主设计应采用 binary mask |
| “executor-agnostic repair interface” | 本文训练和执行固定使用 Qwen-Image-ControlNet-Inpainting |

---

## 23. 最终推荐表述

英文：

> LoState is designed as a verification-enabling reflective state language rather than a rendering format, ordinary layout JSON, or graph learning model. It maintains a dual-role schema: Goal LoState specifies what should be satisfied, while Observed LoState records what is actually generated through a programmatic observer. The reflective loop reviews the two states through LoReview and asks a unified Qwen2.5-VL planner to produce both RepairPlan and a structured VLM Mask Plan. The system then rasterizes this plan into a binary control mask for Qwen-Image-ControlNet-Inpainting, re-observes the edited semantic layout, and accepts the repair only when the new state improves without introducing new hard violations.

中文：

> LoState 被设计为一种面向验证的反思式状态语言，而不是渲染格式、普通 layout JSON 或图学习模型。它采用 Goal / Observed 双角色 schema：Goal LoState 描述布局应该满足什么，Observed LoState 通过程序化观察器记录生成结果实际发生了什么。反思闭环通过 LoReview 对二者进行双轨状态审查，并由统一的 Qwen2.5-VL Planner 同时输出 RepairPlan 与结构化 VLM Mask Plan。系统随后将该 mask_spec 栅格化为 Qwen-Image-ControlNet-Inpainting 所需的二值 control_mask，执行局部修复，再通过重新观察与验证决定接受或回滚。

