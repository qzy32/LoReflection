# 06 Qwen-Image Architecture In-Context Control：方法与实验最终版



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
