# Palette + Metric Contract Audit Summary

## 1. Palette 是什么

当前有效 palette 是 frozen semantic registry 里的 category-to-RGB 映射：
`artifacts/semantic_registry_v2/palette_frozen.json`。代码通过
`loreflection.semantic_registry.load_registry()` 读取它。

## 2. Contract 是什么

Palette contract 是程序侧约束：renderer、target image、quantizer、parser、eval
必须使用同一套 frozen category-to-RGB mapping。它不是 Qwen 能自动读取的文件。

## 3. palette_contract_ref 是否能直接被 Qwen 读取

不能。Qwen/DiffSynth 训练读到的是 `prompt` 字符串、`context_image` 条件图、
以及 `image` 监督图。`palette_contract_ref` 只是给程序、审计和复现用。

## 4. palette_control 怎么给 Qwen

已新增 `prompt_compiler_v2.py`，将统一的 `Palette_Control.` 文本编译进 metadata
里的 prompt。Qwen 真正看到的是这个 prompt 文本。

## 5. compiled_prompt 结构

```text
Context_Control. ... user intent ...

Architecture_Control. Follow the architecture condition image for room boundary, walls, doors, windows, clearance regions, and non-placeable regions.

Palette_Control. Generate a fixed-palette semantic layout only. Use the frozen category-to-color semantic palette. ... Active semantic categories: ...
```

## 6. active_palette_entries 是什么

`active_palette_entries` 是当前样本 required furniture categories 对应的 RGB 子集。
它写入 prompt package 供程序和审计使用；默认不把 RGB 数字塞进 prompt。

## 7. unknown color rate 和 class-color confusion 的区别

unknown color rate 只检查输出颜色是否在 frozen palette 里。
class-color confusion 检查输出颜色对应的类别是否正确。

例子：desk 被量化成 double_bed 的 RGB 时，unknown color rate 仍然是 0，
但 class-color 是错的。

## 8. 当前是否发现类别颜色混淆

本地快照没有服务器 quantized prediction outputs，所以本地报告是
`NOT VERIFIED locally`。已新增 class-color confusion audit；在 A800 上有 prediction
和 quantized outputs 时会生成 confusion matrix。

## 9. 当前 Qwen 输入分辨率

当前 metric_v2 baseline 口径是 `256x256`。

## 10. context 和 target 是否同 transform

已知 metric_v2 audit 结果显示合同通过：

```text
metric_transform_exists_rate = 1.0
target_bbox_fallback_rate = 0.0
```

## 11. 1m 对应多少 pixel

默认 8m / 256px fixed metric canvas 下：

```text
1m = 32px
1px = 0.03125m
```

大房间可能进入 10m/12m bucket，必须按每条
`architecture.metric_transform.pixels_per_meter` 读取。

## 12. world-pixel-world roundtrip error

已知 metric_v2 audit 快照：

```text
roundtrip_error_p95_m = 0.01956249497439548
```

## 13. 是否存在错误缩放风险

metric_v2 的显式 transform 解决了 normalized_v1 的主要缩放风险。
P1-1000 前仍建议在 A800 上用真实数据重跑 metric transform audit。

## 14. 规则模板 prompt 是否正确

本地快照缺少服务器 P1 metadata，因此本地没有完整重算。
已新增 rule-template correctness audit，服务器数据存在时可以直接跑。

## 15. 哪些 prompt 有风险

审计器会标记这些风险词：

```text
specific color palette designated for elderlyroom
correct color palette
beautiful
modern
cozy
wood
fabric
material
texture
```

这些会被视为 appearance/style/color wording risk。

## 16. 是否建议现在进入 P1-1000

不建议。应先在 A800 上重跑 palette/metric/rule prompt audits，并优先跑
compiled_palette 对照训练。

## 17. 是否建议跑 compiled_palette 版本训练

建议。训练脚本草案已准备，但本轮没有启动训练。
