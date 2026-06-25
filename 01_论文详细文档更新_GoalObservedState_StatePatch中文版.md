<!-- LoReflection updated on 2026-06-25: final unified Goal State Constructor single-module version + Observed State Builder + StatePatch loop -->

# 01 论文详细文档更新：Goal State 构造、Qwen-Image Architecture In-Context Control、Observed State 与 StatePatch 闭环

## 0. 本版最终采用路线

本版明确采用如下主线：

```text
User instruction
+ Architecture JSON
+ frozen semantic registry
        ↓
Goal State Constructor
        ↓
Goal LoState
  - furniture_slots
  - goal_constraints
  - verification_profile
        ↓
Prompt Compiler
        ↓
Qwen-Image Architecture In-Context Control initial fixed-palette semantic layout generation
        ↓
Qwen output parser / existing layout JSON converter
        ↓
layout JSON
        ↓
Observed State Builder
        ↓
Observed LoState
  - furniture_instances
  - measured_relations
  - hard_constraint_evidence
        ↓
Goal-Observed Comparator + LoRAM
        ↓
LoReview
        ↓
VLM StatePatch Editor
        ↓
StatePatch / local target object state
        ↓
StatePatch Executor resolves the patch in the Observed LoState view and writes it back to candidate layout JSON / scene JSON
        ↓
Programmatic Verifier + VLM Reviewer
        ↓
AcceptanceController accept / rollback / retry
        ↓
Final layout JSON / scene JSON + rebuilt Final Observed LoState
```

最重要的边界：

```text
Goal State Constructor：
  单一目标构造模块。
  输入 User instruction + Architecture JSON + semantic registry。
  输出非数值 Goal LoState。
  内部可做 slot 抽取、约束补全、schema 校验，但这些只是实现细节，不作为论文主流程阶段。

Goal LoState：
  目标约束状态，描述“应该满足什么”。
  不带完整家具数值坐标、朝向、bbox、footprint。

Observed LoState：
  当前测量状态，描述“当前布局实际是什么”。
  从 layout JSON 构造，带 center / size / orientation / footprint。
  通过 Relation Measurer 计算 measured_relations 和 hard_constraint_evidence。

LoReview：
  比较 Goal 的目标约束和 Observed 的测量证据，输出差异诊断。

StatePatch：
  VLM 针对 LoReview 输出的局部数值修复动作。

Program：
  负责 StatePatch 的目标解析、candidate layout JSON / scene JSON 写回、重建 Observed LoState、几何重算、验证和回滚。
```

本版继续坚持：

```text
Qwen-Image Architecture In-Context Control：只负责初始 fixed-palette semantic layout generation；输入为 compiled_text_prompt + architecture_condition_image。
Qwen output parser：负责把 Qwen-Image Architecture In-Context Control 结果转成 layout JSON，本模块视为已有。
Observed State Builder：负责从 layout JSON 构造 Observed LoState，并计算关系和硬约束证据。
VLM：负责软语义审查、局部修复决策、StatePatch 输出。
Program：负责确定性执行、安全验证、回滚和渲染。
```

不再采用历史路线：

```text
不采用：RepairPlan + mask_spec → Mask Tensor Adapter → Qwen-Image-ControlNet-Inpainting 作为局部修复主路径。
不采用：Qwen-Image / DiffSynth 作为 MOVE / ROTATE / SCALE / REMOVE / REPLACE 的 layout-level repair executor。
不采用：让 VLM 重写完整 Edited LoState，然后系统完全相信它。
不采用：程序自己替 VLM 决定如何修复。
不采用：把 functional_relations 作为与 object-object / object-architecture 平行的单独关系表。
不采用：把 Goal State Constructor 在论文主流程中拆成多个阶段。
```

采用的新核心判断是：

```text
Goal 用于表达目标约束。
Observed 用于表达当前测量事实。
LoReview 用于表达二者差异。
VLM 负责修复智能。
程序负责执行安全。
```


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

### 数据成套构造

每个训练样本必须来自同一个原始房间，不能混配：

```text
raw 3D-FRONT / PlanJSON / layout JSON
        ↓
canonicalization
        ↓
Architecture JSON + layout JSON
        ↓
Goal label extractor
        ↓
Goal LoState
        ↓
Prompt Compiler
        ↓
compiled_text_prompt

Architecture JSON
        ↓
palette-exact renderer
        ↓
architecture_condition_image

layout JSON
        ↓
palette-exact renderer
        ↓
target_semantic_layout_image
```

最终训练记录：

```csv
image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs
target/room_0001_target_semantic.png,"Context_Control. Room type: bedroom. Required furniture: one double bed, two nightstands, one wardrobe, and one desk. Place the nightstands near the bed. Keep the door and window clearance areas free. Use only the frozen semantic furniture categories and palette.",cond/room_0001_arch_condition.png,room_0001,meta/room_0001_goal.json,meta/room_0001_prompt_package.json,meta/room_0001_verifier_refs.json
```

字段含义：

```text
image：target_semantic_layout_image，训练监督目标。
prompt：Goal LoState 编译后的 compiled_text_prompt，建议加 Context_Control. 前缀。
context_image：Architecture JSON 渲染出的 architecture_condition_image。
```

### Prompt Compiler 约束路由

Prompt Compiler 只接收 Goal LoState，并将非数值 goal_constraints 编译为 Qwen 文本提示。它不重新解析用户需求，也不重新读取完整 Architecture JSON。用户需求已经被 Goal State Constructor 融入 Goal LoState；建筑几何由 Architecture JSON 渲染为 condition image。

进入 prompt：

```text
room_type
required furniture slots
required furniture counts
main object / primary anchor
preferred pairwise relations
language-friendly region relations
simple global guidance
frozen category / palette binding
```

进入 architecture_condition_image：

```text
room boundary
solid walls
doors
windows
door clearance regions
window clearance regions
non-placeable regions
room mask
```

只进入 Verifier：

```text
collision_area == 0
inside_room == true
door_swing_clearance_violation == 0
window_swing_clearance_violation == 0
room_walkable_component_count_60cm <= 1
具体 clearance cm 阈值
具体 bed_side_clearance_ratio
具体 dining_table_two_side_clearance
具体 furniture center / size / orientation / footprint / bbox
```

### 训练方法

使用 DiffSynth-Studio 的 Qwen-Image In-Context-Control-Union 分支进行 LoRA 训练。核心配置为：

```bash
accelerate launch examples/qwen_image/model_training/train.py \
  --dataset_base_path data/loreflection_qwen_arch_control \
  --dataset_metadata_path data/loreflection_qwen_arch_control/metadata.csv \
  --data_file_keys "image,context_image" \
  --max_pixels 1048576 \
  --dataset_repeat 50 \
  --model_id_with_origin_paths "Qwen/Qwen-Image:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image:text_encoder/model*.safetensors,Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors" \
  --learning_rate 1e-4 \
  --num_epochs 5 \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path "./models/train/loreflection_qwen_arch_incontext_lora" \
  --lora_base_model "dit" \
  --lora_target_modules "to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1" \
  --lora_rank 64 \
  --lora_checkpoint "models/DiffSynth-Studio/Qwen-Image-In-Context-Control-Union/model.safetensors" \
  --extra_inputs "context_image" \
  --use_gradient_checkpointing \
  --find_unused_parameters
```

第一版建议从已有 In-Context-Control-Union LoRA checkpoint 继续训练；如果要从零训练 architecture-control LoRA，可以移除 `--lora_checkpoint`。

### Loss function

本模块不是语言模型 SFT，不使用 token cross entropy。Qwen-Image Architecture In-Context Control 使用 DiffSynth-Studio 的 diffusion / flow matching SFT loss：

```text
L_Qwen = FlowMatchSFTLoss(
    prompt = compiled_text_prompt,
    context_image = architecture_condition_image,
    input_image = target_semantic_layout_image
)
```

Prompt Compiler 第一阶段不训练，只用规则模板。如果后续训练 Prompt Compiler，才单独作为 `Goal LoState → compiled_text_prompt / PromptPackage` 的语言模型 SFT 任务，loss 为 token-level cross entropy。

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

## 1. 摘要更新

室内家具布局生成与编辑不仅要求生成视觉上合理的布局图，还需要满足对象完整性、功能使用、建筑避让、几何合法性和真实可用性。现有 one-shot generation / one-shot editing 方法通常将生成结果视为最终答案，缺少对输出状态的结构化回读、目标约束对齐、问题诊断和可控局部修复能力。

本文提出 **LoReflection**，一个基于 LoState 的闭环室内布局生成与编辑框架。LoReflection 首先通过 **Goal State Constructor** 从用户需求、建筑结构和冻结语义注册表中构造 **Goal LoState**。Goal LoState 是一个非数值目标约束状态，包含目标家具 slots、统一的 goal_constraints 和 verification_profile，而不是完整家具坐标。随后，Qwen-Image 只负责初始 fixed-palette semantic layout generation，其生成结果被已有解析模块转成 layout JSON。系统再通过 **Observed State Builder** 从 layout JSON 构造带数值几何的 Observed LoState，并计算 measured_relations 与 hard_constraint_evidence。最后，LoReflection 将 Goal 的目标约束与 Observed 的测量证据进行比较，生成 LoReview，并由 VLM StatePatch Editor 输出局部 StatePatch。StatePatch 由 VLM 针对 Observed LoState 中的对象字段输出；Executor 通过 target_ref 确定性查表定位底层 layout object，并由 Write-back Serializer 写入 candidate layout JSON / scene JSON。系统随后从 candidate layout JSON / scene JSON 重新构建 Observed LoState，只有在 Programmatic Verifier 与 VLM Reviewer 通过后才被 AcceptanceController 接受。

本文的核心贡献是：

1. 提出 **Goal-Observed 双状态对齐框架**：Goal LoState 表示目标约束，Observed LoState 表示当前测量事实，LoReview 表示二者差异。
2. 提出 **Goal State Constructor**：将 User instruction、Architecture JSON 和 semantic registry 转换为不带家具坐标、但可绑定 verifier 的目标约束状态。
3. 提出 **Observed State Builder**：从 layout JSON 构造 Observed LoState，并从几何中确定性计算 measured_relations 和 hard_constraint_evidence。
4. 提出 **统一 goal_constraints 表示**：将 requirement、pairwise、region、global 四类约束统一到一个表中，功能语义作为 intent_tag，而不是单独的 functional_relations。
5. 提出 **VLM StatePatch Editor + StatePatch Executor + Programmatic Verifier + AcceptanceController** 的安全局部修复机制，使 VLM 的修复决策可执行、可验证、可回滚。
6. 提出 **Qwen-Image Architecture In-Context Control 初始生成模块**：将 Goal LoState 编译得到的文本目标与 Architecture JSON 渲染得到的 palette-exact architecture condition image 结合，生成初始家具语义布局图。
7. 提出面向布局可用性的 LoReflection-Eval，从 Scene Quality、Constraint Satisfaction、Geometric Validity、Practical Usability 与 StatePatch Editing Quality 多维度评价生成和编辑质量。

---

## 2. 与现有关系/约束式布局生成方法的关系

本方法借鉴了多类 relation-aware / constraint-aware layout generation 的思想，但不照搬其执行路径。

### 2.1 借鉴 InstructScene / scene-graph 方法

InstructScene 类方法的关键思想是：不要只依赖隐式生成分布，而是显式建模对象类别和对象关系，再生成具体布局。LoReflection 吸收其思想，把 User instruction 和 Architecture 转成 Goal LoState 中的 furniture_slots 与 goal_constraints。

区别是：

```text
InstructScene-like methods:
semantic graph prior → layout decoder → positions / sizes / orientations

LoReflection:
Goal LoState constraints → Qwen prompt → layout JSON → Observed State → LoReview → StatePatch
```

LoReflection 不把关系图直接作为布局输出，而是把它作为目标约束状态，后续通过 Observed State 的几何测量来检查是否满足。

### 2.2 借鉴 LayoutVLM 的可执行约束思想

LayoutVLM 让 VLM 生成可执行的空间约束程序，再通过优化得到最终布局。LoReflection 不要求 VLM 输出 Python constraint program，也不把 solver 作为主生成器，而是把可执行思想转为 Goal LoState 中的 `verification` 字段。

映射关系：

```text
against_wall        → predicate: against, verification: object_wall_contact
point_towards       → predicate: facing, verification: pair_relation / facing_angle
distance_constraint → predicate: near / distance_range / avoid_overlap
align_with          → predicate: aligned_with / parallel_to
no collision        → global constraint: no_collision
```

因此，LoReflection 的 goal_constraints 不是纯自然语言，而是可被后续 Relation Measurer / Programmatic Verifier 检查的约束对象。

### 2.3 借鉴 DirectLayout 的对象抽取和空间推理

DirectLayout 最终输出数值布局，但它的 reasoning 思想仍可借鉴：先识别对象，再判断空间关系，最后组织结构化输出。

LoReflection 不借鉴它的数值输出，而是借鉴其前置推理：

```text
entity extraction → furniture_slots
spatial reasoning → goal_constraints
answer organization → Goal LoState JSON
```

也就是说，Goal State Constructor 可以学习“先理解对象和空间意图，再组织结构化输出”，但最终只输出非数值 Goal LoState。

### 2.4 借鉴 OptiScene / 3D-SynthPlace 的高层空间语义

OptiScene / 3D-SynthPlace 说明，在具体布局生成前引入 high-level spatial descriptions 有助于提升布局可用性。

LoReflection 的处理方式更收敛：

```text
high-level spatial description
        ↓
goal_constraints
```

高层空间语义不作为独立状态保存，也不作为单独流程阶段；它只用于帮助 Goal State Constructor 生成更合理的 goal_constraints。

### 2.5 借鉴 Function2Scene 的功能可用性思想

Function2Scene 的启发不是新增一张 `functional_relations` 表，而是把“空间是否支持使用者活动”纳入每条约束的 intent 和 verification 中。

因此：

```text
sofa facing TV
= pairwise constraint + intent_tag: viewing

wardrobe front clearance
= region constraint + intent_tag: storage_access

room walkable connected
= global constraint + intent_tag: circulation
```

---

## 3. Goal LoState：目标约束状态

Goal LoState 的最终结构为：

```json
{
  "schema_version": "goal-lostate-v2",
  "state_role": "goal",
  "metadata": {},
  "architecture_ref": {},
  "semantic_registry_ref": {},
  "room_type": "bedroom",
  "furniture_slots": [],
  "goal_constraints": [],
  "verification_profile": {},
  "prompt_compilation_policy": {}
}
```

### 3.1 furniture_slots

`furniture_slots` 表示目标家具需求，而不是 observed instance。

```json
{
  "slot_id": "goal:bed_main",
  "category": "double_bed",
  "category_id": 12,
  "required": true,
  "count": 1,
  "role": "primary_anchor",
  "source": "user_instruction",
  "numeric_pose": null
}
```

Goal slot 禁止包含：

```text
center_m
size_m
orientation_deg
footprint_m
bbox_m
mask_ref
observed_instance_id
```

### 3.2 goal_constraints

不再拆成 desired_relations / functional_relations / architectural_relations。统一使用 `goal_constraints`。

每条 constraint 的统一结构：

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

四类 constraint：

```text
requirement：对象和数量
pairwise：家具-家具关系
region：家具-建筑 / 家具-clearance / 家具-free-space 关系
global：全局硬约束
```

功能语义只作为：

```text
intent_tag
```

而不是平行的 functional_relations。

---

## 4. Goal State Constructor：单一模块设计

### 4.1 模块定义

Goal State Constructor 是 LoReflection 中负责把用户需求和建筑结构转换为目标约束状态的模块。

输入：

```text
User instruction
+ Architecture JSON
+ semantic registry
```

输出：

```text
Goal LoState
```

整体定义为：

```text
Goal State Constructor:
User instruction + Architecture JSON + semantic registry → Goal LoState
```

Goal State Constructor 在线上只暴露一个接口：

```python
def construct_goal_state(
    user_instruction: str,
    architecture_json: dict,
    semantic_registry: dict
) -> dict:
    ...
```

它内部可以执行以下实现细节：

```text
slot 抽取
类别映射
建筑约束补全
room prior 补全
goal_constraints 构造
schema validation
```

但这些不作为论文主流程中的独立阶段。

### 4.2 设计原则

Goal State Constructor 不直接预测数值布局，而是生成一个非数值目标约束状态。

它不输出：

```text
center_m
size_m
orientation_deg
footprint_m
bbox_m
mask_ref
```

它输出：

```text
应该有哪些家具；
哪些家具之间应该靠近、面对、成组或对齐；
哪些家具应该靠墙、靠窗或避让门窗；
哪些区域不能被家具占用；
哪些通行和使用空间必须保留；
每条约束后续应该如何验证。
```

最终一句话：

```text
Goal LoState stores desired constraints, not object poses.
```

中文：

```text
Goal LoState 存的是目标约束，不是家具位置答案。
```

### 4.3 Goal State Constructor 的训练标签构造

Goal State Constructor 的训练标签不需要完全人工标注，可以从已有真实布局或历史 layout JSON 中自动构造。

数据构造流程为：

```text
3D-FRONT / existing layout JSON
        ↓
rule-based extraction of object-object / object-region / global constraints
        ↓
Goal LoState label construction
        ↓
LLM prompt examples or SFT data
        ↓
Goal State Constructor
```

也就是说：

```text
真实布局不是直接作为 Goal；
真实布局用于反推出“这种房间通常应该满足哪些关系约束”。
```

自动抽取规则示例：

```text
bed 与 solid wall 距离小于阈值
→ bed against solid wall

nightstand 与 bed edge_distance 小于阈值
→ nightstand adjacent_to bed

sofa 的 front_dir 指向 TV，facing_angle 小于阈值
→ sofa facing TV

desk 与 window distance 小于阈值
→ desk near window

wardrobe 前方存在足够 free space
→ wardrobe front_accessible

layout 中所有 furniture 无碰撞
→ no_collision global constraint

layout 中家具均不与 door clearance 相交
→ door_clearance_free global / region constraint
```

### 4.4 输出示例

```json
{
  "schema_version": "goal-lostate-v2",
  "state_role": "goal",
  "room_type": "bedroom",
  "furniture_slots": [
    {
      "slot_id": "goal:bed_main",
      "category": "double_bed",
      "category_id": 12,
      "required": true,
      "count": 1,
      "role": "primary_anchor",
      "source": "user_instruction",
      "numeric_pose": null
    }
  ],
  "goal_constraints": [
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
    },
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
  ]
}
```

---

## 5. Observed State Builder：从 layout JSON 到当前测量状态

Observed State Builder 的输入为：

```text
layout JSON
+ Architecture JSON
+ semantic registry
+ verification_profile
```

输出为：

```text
Observed LoState
```

流程：

```text
layout JSON
        ↓
Observed State Builder
        ↓
furniture_instances
        ↓
Relation Measurer
        ↓
measured_relations
        ↓
Programmatic Verifier
        ↓
hard_constraint_evidence
```

它负责从 layout JSON 的家具类别、中心、尺寸、朝向、polygon / footprint 等字段中构造当前状态，并计算关系。

### 5.1 Observed LoState 结构

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

### 5.2 furniture_instances

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

### 5.3 measured_relations

Object-object 示例：

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

Object-region 示例：

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

### 5.4 hard_constraint_evidence

```json
{
  "hard_constraint_evidence": {
    "oob": [],
    "collision": [],
    "door_window_blocking": [
      {
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

## 6. Goal-Observed Comparator 与 LoReview

Comparator 比较：

```text
Goal LoState.goal_constraints
        vs
Observed LoState.measured_relations + hard_constraint_evidence
```

输出：

```text
LoReview
```

基本流程：

```text
goal slot ↔ observed instance 对齐
        ↓
对每条 goal_constraint 找对应 observed evidence
        ↓
判断 satisfied / violated / missing_target / not_applicable / unknown
        ↓
生成 LoReview issue
```

LoReview 示例：

```json
{
  "review_id": "review_round_0",
  "issues": [
    {
      "issue_id": "issue_001",
      "constraint_id": "gc_bed_avoid_door_clearance",
      "issue_type": "opening_clearance_violation",
      "severity": "hard",
      "involved_refs": ["obs:bed_001", "arch:door_001_clearance"],
      "evidence": {
        "overlap_area_m2": 0.32
      },
      "suggested_action_types": ["TRANSLATE", "ROTATE"],
      "protected_refs": ["obs:wardrobe_001", "obs:desk_001"]
    }
  ]
}
```

---

## 7. VLM StatePatch Editor、Write-back Serializer 与安全执行

VLM StatePatch Editor 输入：

```text
Goal LoState
Observed LoState
LoReview
layout render / semantic map
optional user edit instruction
```

输出：

```text
StatePatch over the Observed LoState view
```

注意：StatePatch 使用 Observed LoState 的 `target_ref` 来定位对象，但它不是直接修改 Observed LoState 文件。Executor 会通过 Observed LoState 中的 provenance 信息，将 `target_ref` 映射到底层 layout JSON / scene JSON 的对象 ID，然后把修改写入 candidate layout JSON / scene JSON。

### 7.1 StatePatch 示例

```json
{
  "patch_id": "patch_0001",
  "patch_target_space": "observed_lostate_view",
  "execution_target_space": "layout_json",
  "source_observed_state_id": "observed_round_0",
  "action_type": "TRANSLATE",
  "target": {
    "target_ref": "obs:bed_001",
    "expected_category": "bed"
  },
  "reason": "bed overlaps the door clearance area",
  "state_field_updates": {
    "center_m": {
      "update_mode": "relative_delta",
      "delta_m": [0.6, 0.0]
    }
  },
  "constraints_to_satisfy": [
    "gc_bed_avoid_door_clearance",
    "gc_no_collision",
    "gc_inside_room"
  ],
  "protected_refs": [
    "obs:wardrobe_001",
    "obs:desk_001"
  ]
}
```

字段解释：

```text
state_field_updates：状态字段更新表，表示这次局部 patch 要改目标对象的哪些字段。
center_m：要修改目标对象在布局平面上的中心点。
update_mode = relative_delta：相对增量更新，不是给一个全新绝对坐标，而是在旧坐标上加一个变化量。
delta_m = [0.6, 0.0]：在当前中心点基础上，沿第一个平面坐标移动 0.6 米，第二个平面坐标不变。
patch_target_space = observed_lostate_view：该 patch 是 VLM 基于 Observed LoState 视图写出的。
execution_target_space = layout_json：程序实际执行时必须写回 layout JSON / scene JSON。
```

### 7.2 安全执行流程

StatePatch Executor / Write-back Serializer 只负责：

```text
1. validate_patch_schema(patch)
2. resolve_target_ref(patch.target.target_ref, observed_state)
3. map observed target_ref → source_object_id / source_json_path
4. check_allowed_fields(action_type, state_field_updates)
5. translate state_field_updates → layout JSON field updates
6. write updates to candidate layout JSON / scene JSON
7. rebuild Observed LoState from candidate layout JSON / scene JSON
8. recompute_geometry / measured_relations / hard_constraint_evidence
9. run_programmatic_verifier(candidate_observed_state)
10. check_protected_refs(old_observed_state, candidate_observed_state, patch.protected_refs)
11. return ACCEPT / FAIL with structured reason
```

它不替 VLM 决定怎么修。VLM 负责修复智能，程序负责执行安全。

### 7.3 失败与回滚

如果 `target_ref` 无法解析到底层 layout object，返回 `PATCH_RESOLVE_FAIL`；如果 `state_field_updates` 无法映射到 layout JSON 字段，返回 `PATCH_FIELD_MAPPING_FAIL`；如果写回后引入碰撞、越界、挡门或破坏 protected_refs，返回 `PATCH_VERIFY_FAIL` / `PATCH_PRESERVE_FAIL`。所有失败都丢弃 candidate layout JSON / scene JSON，并回滚到上一轮 current layout JSON / scene JSON。

---

## 8. 最终论文定位

本文最终定位为：

```text
LoReflection is a closed-loop indoor layout generation and editing framework where a non-numeric Goal LoState specifies verifier-bindable desired constraints, a concrete Observed LoState measures the current layout from JSON geometry, and a VLM repairs local differences through StatePatch under programmatic verification.
```

中文：

```text
LoReflection 是一个闭环室内布局生成与编辑框架：非数值 Goal LoState 表达可验证目标约束，具体 Observed LoState 从 layout JSON 几何中测量当前状态，VLM 通过 StatePatch 修复局部差异，并由程序化验证保证安全。
```
