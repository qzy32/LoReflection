<!-- LoReflection updated on 2026-06-25: final LoState v7 with single-module Goal State Constructor and Observed relation measurement -->

# 02 LoState / GoalObserved / StatePatch 设计文档 v8：目标约束状态、Architecture In-Context 生成与当前测量状态

## 0. 本版核心结论

LoState 仍然是 LoReflection 的统一状态语言，但本版进一步明确两个核心 role：

```text
1. Goal LoState
   symbolic constraint state
   表示“应该满足什么”
   不带完整家具数值位置

2. Observed LoState
   concrete measured state
   表示“当前布局实际是什么”
   从 layout JSON 构造
   带 center / size / orientation / footprint / measured_relations / hard_constraint_evidence
```

两者的比较产生 LoReview：

```text
Goal LoState.goal_constraints
        vs
Observed LoState.measured_relations + hard_constraint_evidence
        ↓
LoReview
        ↓
StatePatch
```

本版最重要的修正：

```text
Goal State Constructor 是一个单一模块。
内部可做 slot 抽取、约束补全和 schema 校验，但不在 LoState 设计里拆成多个主流程阶段。
```

局部修复主路径为：

```text
VLM StatePatch Editor → StatePatch → StatePatch Executor + Write-back Serializer → candidate layout JSON / scene JSON → rebuild Observed LoState → Verifier / Reviewer / Acceptance
```

### StatePatch v1.2：直接面向 Observed LoState 对象字段的局部补丁

StatePatch v1.2 的核心设计是：**VLM 直接针对 Observed LoState 中某个家具对象的数值字段输出局部修改动作**。这不是完整 JSON 重写，也不是底层 layout JSON 路径编辑。

推荐 schema：

```json
{
  "patch_id": "patch_0001",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "obs_state_round_0",
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

字段解释：

| 字段 | 含义 |
|---|---|
| `patch_target_space` | patch 是针对 Observed LoState 视图写的 |
| `execution_target_space` | 真正写回的是 layout JSON / scene JSON |
| `target.target_ref` | VLM 要修改的 observed instance ID |
| `target.expected_category` | 防止 target_ref 对错对象的类别校验 |
| `state_field_updates` | 要改哪些 Observed LoState 数值字段 |
| `update_mode` | 更新方式，如 `relative_delta` 或 `absolute` |
| `delta_m` | 以米为单位的增量 |
| `protected_refs` | 不能被修改的非目标对象 |

允许的 `state_field_updates`：

```text
center_m：用于 TRANSLATE
orientation_deg：用于 ROTATE
size_m：用于 SCALE / REPLACE
category / asset_id：用于 REPLACE
new_instance：用于 ADD
```

不允许 VLM 输出：

```text
完整 Edited LoState
完整 layout JSON
source_json_path
底层工程 uid
未经 schema 约束的自由文本修复描述
```

其中 `source_json_path` 和底层 uid 由程序从 Observed LoState 的 provenance 字段查表获得，不要求 VLM 生成。

### Executor 与 Write-back Serializer 的确定性执行规则

Executor 不训练，不做智能规划，不替 VLM 决定怎么修。它只做确定性执行：

```text
1. 读取 VLM 输出的 StatePatch。
2. 用 target_ref 在 Observed LoState.furniture_instances 中查找目标对象。
3. 校验 expected_category 是否匹配。
4. 读取目标对象保存的 source_object_id / source_json_path。
5. 根据字段映射表把 state_field_updates 转成底层 layout JSON 字段更新。
6. 在 candidate layout JSON / scene JSON 上写入更新。
7. 从 candidate layout JSON / scene JSON 重新构建 Observed LoState。
8. 运行 Programmatic Verifier / VLM Reviewer。
9. 通过则 accept；失败则 rollback。
```

典型映射：

| Observed LoState 字段 | layout JSON / scene JSON 字段 |
|---|---|
| `center_m = [x, z]` | `position = [x, y, z]` 中的 x/z |
| `orientation_deg` | `rotation_y_deg` 或 quaternion |
| `size_m = [w, d]` | `size = [w, h, d]` 中的 w/d |
| `category` | `category` |
| `asset_id` | `asset_id` / `jid` |

失败码：

```text
PATCH_SCHEMA_INVALID：StatePatch 格式不合法。
PATCH_TARGET_NOT_FOUND：target_ref 在 Observed LoState 中找不到。
PATCH_CATEGORY_MISMATCH：expected_category 与目标对象类别不一致。
PATCH_SOURCE_MAPPING_FAIL：无法从 observed object 映射到底层 layout object。
PATCH_FIELD_MAPPING_FAIL：state_field_updates 无法映射到底层字段。
PATCH_WRITEBACK_FAIL：candidate layout JSON 写回失败。
PATCH_REBUILD_FAIL：无法从 candidate layout JSON 重建 Observed LoState。
PATCH_VERIFY_FAIL：写回后违反碰撞、越界、挡门等硬约束。
PATCH_NO_IMPROVEMENT：没有改善 LoReview 中的问题。
```

这些失败都必须显式返回给下一轮 VLM StatePatch Editor，不能由程序私自猜测或自动修改其他对象。

---

## 1. LoState 的边界

LoState 包含两类状态：

```text
Goal LoState：目标约束状态，描述应该满足什么。
Observed LoState：当前测量状态，描述当前布局实际上是什么。
```

LoState 不包含：

```text
LoReview
StatePatch
Patch execution log
Verifier report
Acceptance decision
Final3DState
```

这些都是 LoState 外部结构。

---

## 2. Architecture JSON 的职责



## Qwen-Image Architecture In-Context Control 方法

### 模块定位

Qwen-Image Architecture In-Context Control 是 LoReflection 的初始生成模块。它只负责生成初始 palette-exact furniture semantic layout image，不负责局部修复，不直接输出家具 JSON，也不直接预测 center / size / orientation。

在线推理输入仍然只有：

```text
User instruction + Architecture JSON
```

系统先构造 Goal LoState，再由 Prompt Compiler 生成文本提示词：

```text
User instruction + Architecture JSON + semantic registry
        ↓
Goal State Constructor
        ↓
Goal LoState
        ↓
Prompt Compiler
        ↓
compiled_text_prompt
```

同时，Architecture JSON 单独渲染为建筑条件图：

```text
Architecture JSON
        ↓
palette-exact architecture renderer
        ↓
architecture_condition_image
```

然后送入 Qwen-Image In-Context-Control-Union：

```text
compiled_text_prompt + architecture_condition_image
        ↓
Qwen-Image Architecture In-Context Control
        ↓
initial semantic layout image
        ↓
layout parser
        ↓
layout JSON / scene JSON
```



Architecture JSON 负责建筑结构：

```text
room boundary
walls
solid walls
doors
windows
door clearance regions
window clearance regions
coordinate transforms
room type
```

Goal LoState 不复制建筑几何，只引用 architecture anchor / region：

```text
arch:door_001
arch:door_001_clearance
arch:window_001
arch:wall_003
arch:solid_wall_group
```

Observed LoState 在计算关系时使用 Architecture JSON 的几何。

---

## 3. Goal LoState v2

### 3.1 顶层结构

```json
{
  "schema_version": "goal-lostate-v2",
  "state_role": "goal",
  "metadata": {
    "task_id": "bedroom_case_001",
    "repair_round": 0,
    "created_by": "goal_state_constructor",
    "user_instruction": "..."
  },
  "architecture_ref": {
    "architecture_id": "arch_0001",
    "coordinate_transform_id": "world_to_image_v1"
  },
  "semantic_registry_ref": {
    "palette_id": "palette_frozen_v2",
    "category_set": "semantic_registry_v2_training_categories",
    "relation_set": "layout_goal_relations_v2"
  },
  "room_type": "bedroom",
  "furniture_slots": [],
  "goal_constraints": [],
  "verification_profile": {},
  "prompt_compilation_policy": {}
}
```

### 3.2 Goal LoState 禁止字段

Goal LoState 不允许包含完整家具数值姿态：

```text
center_m
size_m
orientation_deg
footprint_m
bbox_m
mask_ref
observed_instance_id
```

允许存在：

```text
size_hint
style_hint
priority
intent_tag
threshold_ref
prompt_hint
```

其中 `threshold_ref` 是验收阈值引用，不是家具坐标。

---

## 4. Goal State Constructor 的位置

Goal State Constructor 是产生 Goal LoState 的单一模块：

```text
User instruction + Architecture JSON + semantic registry
        ↓
Goal State Constructor
        ↓
Goal LoState
```

它在线上只暴露一个接口：

```python
def construct_goal_state(
    user_instruction: str,
    architecture_json: dict,
    semantic_registry: dict
) -> dict:
    ...
```

内部实现可以包括：

```text
slot 抽取
类别映射
建筑约束补全
room prior 补全
goal_constraints 构造
schema validation
```

但这些不作为 LoReflection 主流程中的独立 stage，也不写成独立 LoState role。

### 4.1 Goal Constructor 训练标签构造

Goal Constructor 的训练标签可以从真实布局自动构造：

```text
3D-FRONT / existing layout JSON
        ↓
rule-based extraction of object-object / object-region / global constraints
        ↓
Goal LoState label construction
        ↓
LLM prompt examples or SFT data
```

核心思想：

```text
真实 layout JSON 不作为 Goal State 直接使用。
真实 layout JSON 只用于反推这种房间通常应该满足的 slots 和 constraints。
```

---

## 5. furniture_slots

`furniture_slots` 表示目标家具需求。

```json
{
  "slot_id": "goal:bed_main",
  "category": "double_bed",
  "category_id": 12,
  "required": true,
  "count": 1,
  "role": "primary_anchor",
  "source": "user_instruction",
  "size_hint": "queen_or_double",
  "numeric_pose": null
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `slot_id` | 目标对象符号 ID |
| `category` | 冻结语义类别名 |
| `category_id` | semantic registry 中的 ID |
| `required` | 是否必须出现 |
| `count` | 目标数量 |
| `role` | 布局角色 |
| `source` | user_instruction / room_prior / learned_prior |
| `numeric_pose` | 必须为 null |

建议 role：

```text
primary_anchor
support_object
storage
seating
work_surface
dining_surface
appliance
decorative
circulation_sensitive
optional_object
```

---

## 6. goal_constraints

本版不再拆：

```text
desired_relations
functional_relations
architectural_relations
```

统一为：

```text
goal_constraints
```

### 6.1 统一 schema

```json
{
  "constraint_id": "gc_001",
  "constraint_kind": "requirement | pairwise | region | global",
  "domain": "object | object_object | object_region | global",
  "subject": "goal:bed_main",
  "predicate": "avoid_overlap",
  "object": "arch:door_001_clearance",
  "object_kind": "architecture_region",
  "necessity": "required | preferred",
  "priority": 1,
  "intent_tag": "entry_circulation",
  "source": "user_instruction | architecture_constraint | room_prior | learned_prior",
  "verification": {
    "type": "opening_clearance",
    "metric": "overlap_area",
    "pass_condition": "equals_zero",
    "threshold_ref": null
  },
  "prompt_hint": "Do not place the bed in the door clearance region."
}
```

### 6.2 四类 constraint

| constraint_kind | domain | 含义 |
|---|---|---|
| `requirement` | `object` | 对象和数量要求 |
| `pairwise` | `object_object` | 家具-家具关系 |
| `region` | `object_region` | 家具-建筑 / clearance / free-space 关系 |
| `global` | `global` | 全局硬约束 |

功能关系不单独成类，只作为 `intent_tag`：

```text
viewing
sleeping_access
storage_access
working_light
entry_circulation
physical_validity
circulation
```

### 6.3 示例

Requirement：

```json
{
  "constraint_id": "gc_req_bed_main",
  "constraint_kind": "requirement",
  "domain": "object",
  "subject": "goal:bed_main",
  "predicate": "exists",
  "object": "double_bed",
  "object_kind": "category",
  "necessity": "required",
  "priority": 1,
  "intent_tag": "sleeping",
  "source": "user_instruction",
  "verification": {
    "type": "count_match",
    "metric": "matched_instance_count",
    "pass_condition": ">= 1"
  },
  "prompt_hint": "Include one double bed."
}
```

Pairwise：

```json
{
  "constraint_id": "gc_sofa_tv_viewing",
  "constraint_kind": "pairwise",
  "domain": "object_object",
  "subject": "goal:sofa_main",
  "predicate": "facing",
  "object": "goal:tv",
  "object_kind": "furniture_slot",
  "necessity": "preferred",
  "priority": 3,
  "intent_tag": "viewing",
  "source": "room_prior",
  "verification": {
    "type": "pair_relation",
    "metrics": ["center_distance", "facing_angle"],
    "threshold_ref": "sofa_tv_viewing"
  },
  "prompt_hint": "The main sofa should face the TV at a reasonable distance."
}
```

Region：

```json
{
  "constraint_id": "gc_bed_avoid_door_clearance",
  "constraint_kind": "region",
  "domain": "object_region",
  "subject": "goal:bed_main",
  "predicate": "avoid_overlap",
  "object": "arch:door_001_clearance",
  "object_kind": "architecture_region",
  "necessity": "required",
  "priority": 1,
  "intent_tag": "entry_circulation",
  "source": "architecture_constraint",
  "verification": {
    "type": "opening_clearance",
    "metric": "overlap_area",
    "pass_condition": "equals_zero"
  },
  "prompt_hint": "Do not place the bed in the door clearance region."
}
```

Global：

```json
{
  "constraint_id": "gc_no_collision",
  "constraint_kind": "global",
  "domain": "global",
  "subject": "all_furniture",
  "predicate": "no_collision",
  "object": "all_furniture",
  "object_kind": "furniture_set",
  "necessity": "required",
  "priority": 1,
  "intent_tag": "physical_validity",
  "source": "default_verification_policy",
  "verification": {
    "type": "collision",
    "metric": "collision_area",
    "pass_condition": "equals_zero"
  },
  "prompt_hint": "Furniture should not overlap or collide."
}
```

---

## 7. verification_profile

```json
{
  "verification_profile": {
    "unit": "meter",
    "hard_checks": [
      "count_match",
      "inside_room",
      "collision",
      "opening_clearance",
      "circulation"
    ],
    "soft_checks": [
      "object_wall_contact",
      "pair_relation",
      "object_anchor_distance",
      "furniture_use_clearance"
    ],
    "threshold_refs": {
      "against_wall": {
        "metric": "min_edge_distance",
        "max_m": 0.15
      },
      "bed_nightstand_adjacent": {
        "metric": "edge_distance",
        "max_m": 0.45
      },
      "desk_window_near": {
        "metric": "center_to_anchor_distance",
        "max_m": 1.5
      },
      "bed_side_access": {
        "metric": "bed_side_clearance_ratio",
        "min": 0.5
      },
      "wardrobe_front_access": {
        "metric": "front_clearance_depth",
        "min_m": 0.6
      }
    }
  }
}
```

---

## 8. Observed LoState v2

### 8.1 顶层结构

```json
{
  "schema_version": "observed-lostate-v2",
  "state_role": "observed",
  "metadata": {},
  "architecture_ref": {},
  "semantic_registry_ref": {},
  "room_type": "bedroom",
  "furniture_instances": [],
  "measured_relations": [],
  "hard_constraint_evidence": {}
}
```

Observed LoState 从 layout JSON 构造，不是从 Goal 生成。

### 8.2 furniture_instances

```json
{
  "instance_id": "obs:bed_001",
  "source_object_id": "bed_001",
  "category": "double_bed",
  "category_id": 12,
  "center_m": [1.4, 2.0],
  "size_m": [2.0, 1.5],
  "orientation_deg": 90,
  "footprint_m": [[0.65, 1.0], [2.15, 1.0], [2.15, 3.0], [0.65, 3.0]],
  "bbox_m": [0.65, 1.0, 2.15, 3.0],
  "front_dir": [0.0, 1.0],
  "right_dir": [1.0, 0.0]
}
```

### 8.3 measured_relations

Object-object：

```json
{
  "relation_id": "mr_sofa_tv_001",
  "domain": "object_object",
  "subject": "obs:sofa_001",
  "predicate": "facing",
  "object": "obs:tv_001",
  "metrics": {
    "center_distance_m": 2.8,
    "facing_angle_deg": 12.5
  },
  "satisfied": true
}
```

Object-region：

```json
{
  "relation_id": "mr_bed_door_clearance_001",
  "domain": "object_region",
  "subject": "obs:bed_001",
  "predicate": "overlaps",
  "object": "arch:door_001_clearance",
  "metrics": {
    "overlap_area_m2": 0.32
  },
  "matched_goal_constraint": "gc_bed_avoid_door_clearance",
  "satisfied": false,
  "severity": "error"
}
```

### 8.4 hard_constraint_evidence

```json
{
  "hard_constraint_evidence": {
    "oob": [],
    "collision": [
      {
        "type": "collision",
        "subject": "obs:chair_001",
        "object": "obs:table_001",
        "overlap_area_m2": 0.08,
        "severity": "error"
      }
    ],
    "door_window_blocking": [
      {
        "type": "door_clearance_blocking",
        "subject": "obs:bed_001",
        "object": "arch:door_001_clearance",
        "overlap_area_m2": 0.32,
        "severity": "error"
      }
    ],
    "circulation": [
      {
        "type": "walkable_disconnected",
        "metric": "room_walkable_component_count_60cm",
        "value": 2,
        "severity": "error"
      }
    ]
  }
}
```

---

## 9. Observed State Builder

Observed State Builder 的输入：

```text
layout JSON
+ Architecture JSON
+ semantic registry
+ verification_profile
```

输出：

```text
Observed LoState
```

它做四件事：

```text
1. layout JSON 标准化为 furniture_instances；
2. 补齐 footprint / bbox / front_dir / right_dir；
3. 根据几何计算 measured_relations；
4. 根据 verifier 计算 hard_constraint_evidence。
```

注意：这里的四件事是 Observed State Builder 的内部实现，不是 LoReflection 主流程的四个独立模块。

---

## 10. Goal-Observed Comparator

Comparator 输入：

```text
Goal LoState
Observed LoState
Architecture JSON
```

输出：

```text
LoReview
```

比较逻辑：

```text
1. goal slot ↔ observed instance 对齐；
2. 对每条 goal_constraint 找 measured relation 或 hard evidence；
3. 判断 satisfied / violated / missing_target / not_applicable / unknown；
4. 生成 LoReview issue。
```

---

## 11. StatePatch v1.2：针对 Observed LoState 视图的局部修改指令

StatePatch 是 VLM 对局部修复的结构化决策，不是完整场景，也不是最终 layout JSON。它的引用空间是 Observed LoState，因为 VLM 读取的是 Goal LoState、Observed LoState、语义图和 LoReview；它的执行空间是 layout JSON / scene JSON，因为后续渲染、保存、复测和导出都必须依赖可执行场景文件。

统一顶层结构：

```json
{
  "schema_version": "statepatch-v1.2",
  "patch_id": "patch_0001",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "observed_round_0",
  "action_type": "TRANSLATE",
  "target": {
    "target_ref": "obs:bed_001",
    "expected_category": "bed"
  },
  "reason": "bed blocks door clearance",
  "state_field_updates": {},
  "new_instance": null,
  "replacement": null,
  "protected_refs": [],
  "constraints_to_satisfy": [],
  "constraints_to_preserve": [],
  "acceptance_criteria": []
}
```

### 11.1 关键字段解释

```text
patch_target_space = observed_lostate_view
  表示该 patch 是 VLM 基于 Observed LoState 视图写出来的。

execution_target_space = layout_json
  表示程序真正执行时，必须把该 patch 写回 candidate layout JSON / scene JSON。

target.target_ref
  VLM 使用的目标对象引用，例如 obs:bed_001。它来自 Observed LoState。

state_field_updates
  状态字段更新表，表示要改目标对象的哪些状态字段，例如 center_m、orientation_deg、size_m。

update_mode = relative_delta
  相对增量更新，即在旧值基础上加一个变化量。

delta_m
  以米为单位的变化量。例如 [0.6, 0.0] 表示平面第一个坐标增加 0.6 米，第二个坐标不变。
```

### 11.2 TRANSLATE 示例

```json
{
  "schema_version": "statepatch-v1.2",
  "patch_id": "patch_0001",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "observed_round_0",
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
  "reason": "bed_001 overlaps the door clearance area",
  "constraints_to_satisfy": ["door_clearance_free", "inside_room", "no_collision"],
  "protected_refs": ["obs:wardrobe_001", "obs:desk_001"]
}
```

执行语义：如果当前 `center_m = [1.4, 2.0]`，则新中心点为 `[2.0, 2.0]`。程序再把这个二维平面中心点写回 layout JSON / scene JSON 中对应对象的位置字段。

### 11.3 ROTATE 示例

```json
{
  "schema_version": "statepatch-v1.2",
  "patch_id": "patch_0002",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "observed_round_0",
  "action_type": "ROTATE",
  "target": {
    "target_ref": "obs:desk_001",
    "expected_category": "desk"
  },
  "state_field_updates": {
    "orientation_deg": {
      "update_mode": "absolute",
      "value_deg": 90
    }
  },
  "reason": "desk should face the room while preserving chair access",
  "constraints_to_satisfy": ["desk_facing_room", "chair_accessible", "no_collision"]
}
```

### 11.4 ADD 示例

ADD 没有已有 `target_ref`，因此 VLM 输出一个局部 `new_instance`。程序给它分配新的 layout JSON object id，然后 append 到 candidate layout JSON / scene JSON。

```json
{
  "schema_version": "statepatch-v1.2",
  "patch_id": "patch_0003",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "observed_round_0",
  "action_type": "ADD",
  "new_instance": {
    "category": "nightstand",
    "center_m": [1.2, 2.1],
    "size_m": [0.45, 0.45],
    "orientation_deg": 0,
    "relations": [
      {"predicate": "adjacent_to", "object_ref": "obs:bed_001"}
    ]
  },
  "reason": "Goal LoState requires a nightstand beside the bed, but it is missing.",
  "constraints_to_satisfy": ["inside_room", "no_collision", "nightstand_adjacent_to_bed"]
}
```

### 11.5 REMOVE 示例

```json
{
  "schema_version": "statepatch-v1.2",
  "patch_id": "patch_0004",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "observed_round_0",
  "action_type": "REMOVE",
  "target": {
    "target_ref": "obs:extra_chair_002",
    "expected_category": "chair"
  },
  "reason": "The chair is an extra object not required by Goal LoState.",
  "protected_refs": ["obs:bed_001", "obs:desk_001"]
}
```

### 11.6 REPLACE 示例

```json
{
  "schema_version": "statepatch-v1.2",
  "patch_id": "patch_0005",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "observed_round_0",
  "action_type": "REPLACE",
  "target": {
    "target_ref": "obs:chair_001",
    "expected_category": "chair"
  },
  "replacement": {
    "new_category": "armchair",
    "new_size_m": [0.8, 0.8],
    "new_asset_id": "armchair_modern_003",
    "preserve_fields": ["center_m", "orientation_deg"]
  },
  "reason": "The requested object should be an armchair rather than a dining chair.",
  "constraints_to_satisfy": ["inside_room", "no_collision"]
}
```

支持动作：

```text
ADD
REMOVE
TRANSLATE
ROTATE
SCALE
REPLACE
```

---

## 12. StatePatch Executor 与 Write-back Serializer

StatePatch Executor 是确定性程序模块。它不负责生成设计方案，不负责决定如何修复，只负责把 VLM 的局部修复结果安全地写回可执行场景文件。

### 12.1 三层对象关系

```text
layout JSON / scene JSON
  可执行真值：真正被修改、保存、渲染、导出和复测。

Observed LoState
  诊断视图：由 layout JSON / scene JSON 构建，用于给 VLM 理解当前布局、定位问题和生成 StatePatch。

StatePatch
  局部修改指令：引用 Observed LoState 里的 target_ref，但由程序翻译成 layout JSON / scene JSON 的字段更新。
```

### 12.2 Observed ref 到 layout object 的 provenance

Observed LoState 的每个 furniture instance 必须保存回写所需的 provenance：

```json
{
  "instance_id": "obs:bed_001",
  "source_object_id": "layout_bed_42",
  "source_json_path": "$.objects[0]",
  "category": "double_bed",
  "center_m": [1.4, 2.0],
  "size_m": [2.0, 1.5],
  "orientation_deg": 90
}
```

其中：

```text
instance_id / target_ref：VLM 使用的观测对象引用。
source_object_id：layout JSON / scene JSON 中的真实对象 ID。
source_json_path：该对象在 layout JSON / scene JSON 中的位置，用于精确写回。
```

### 12.3 字段映射

Executor 必须有字段映射表：

```text
Observed LoState.center_m        → layout JSON position[x,z] 或 center_m
Observed LoState.orientation_deg → layout JSON rotation_y_deg 或 orientation_deg
Observed LoState.size_m          → layout JSON size[x,z] 或 size_m
Observed LoState.category        → layout JSON category
Observed LoState.asset_id        → layout JSON asset_id
```

如果某个字段没有映射，返回 `PATCH_FIELD_MAPPING_FAIL`，不得猜测写入。

### 12.4 执行顺序

```text
1. validate_patch_schema(patch)
2. resolve_target_ref(patch.target.target_ref, observed_state)
3. read source_object_id / source_json_path from observed_state
4. check_expected_category
5. check_allowed_fields(action_type, state_field_updates)
6. translate state_field_updates to layout JSON field updates
7. write updates to candidate layout JSON / scene JSON
8. rebuild Observed LoState from candidate layout JSON / scene JSON
9. recompute_geometry / measured_relations / hard_constraint_evidence
10. run_programmatic_verifier(candidate_observed_state)
11. check_protected_refs(old_observed_state, candidate_observed_state, patch.protected_refs)
12. return ACCEPT / FAIL with structured reason
```

### 12.5 失败码

| 失败码 | 含义 | 处理 |
|---|---|---|
| `PATCH_SCHEMA_FAIL` | JSON 格式或字段非法 | 回滚，要求 VLM 重新输出 |
| `PATCH_RESOLVE_FAIL` | target_ref 不存在或不唯一 | 回滚，返回候选对象 |
| `PATCH_SOURCE_MAPPING_FAIL` | target_ref 无法映射到 source_object_id / source_json_path | 回滚 |
| `PATCH_FIELD_MAPPING_FAIL` | StatePatch 字段无法映射到底层 layout JSON 字段 | 回滚 |
| `PATCH_FIELD_FAIL` | 修改了不允许字段 | 回滚 |
| `PATCH_WRITEBACK_FAIL` | 写回 candidate layout JSON / scene JSON 失败 | 回滚 |
| `PATCH_REBUILD_FAIL` | 无法从 candidate layout JSON 重建 Observed LoState | 回滚 |
| `PATCH_VERIFY_FAIL` | 引入 OOB / Collision / DoorWindowBlocking | 回滚，返回硬错误 |
| `PATCH_PRESERVE_FAIL` | protected_refs 被破坏 | 回滚 |
| `PATCH_NO_IMPROVEMENT` | 修复目标没有改善 | 回滚，要求重新规划 |
| `PATCH_ACCEPTED` | 修复通过 | candidate layout JSON / scene JSON 成为新当前布局 |

---

## 13. 一句话版本

```text
Goal LoState stores desired constraints; Observed LoState stores measured geometry and evidence; LoReview compares them; StatePatch repairs local differences under verifier control.
```

中文：

```text
Goal LoState 存目标约束；Observed LoState 存当前几何和证据；LoReview 比较二者；StatePatch 在 verifier 控制下修复局部差异。
```
