# Large Training Launch Summary

- alignment critical gates pass: `True`
- sanitized smoke pass: `True`
- raw architecture caveat: raw quantized output still overwrites protected architecture; source-architecture copyback is part of the accepted system contract.

| task | gpu | pid | metadata | output | log |
|---|---:|---:|---|---|---|
| full_semantic_compiled_main | 0 | 1039353 | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small_metric_v2_full_semantic_compiled/metadata.csv` | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_full_semantic_compiled_main` | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_full_semantic_compiled_main/logs/nohup_train.log` |
| full_semantic_no_relation_ablation | 1 | 1039355 | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small_metric_v2_full_semantic_compiled/metadata_no_relation.csv` | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_full_semantic_compiled_no_relation` | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_full_semantic_compiled_no_relation/logs/nohup_train.log` |
| furniture_only_compiled_ablation | 2 | 1039358 | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_p1_small_metric_v2_full_semantic_compiled/metadata_furniture_only_compiled.csv` | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_furniture_only_compiled` | `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/outputs/qwen_arch_incontext_p1_furniture_only_compiled/logs/nohup_train.log` |
