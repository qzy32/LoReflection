#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path('/wuqingyaoa800/qiuziyan/LoReflection_arch_p0') if Path('/wuqingyaoa800/qiuziyan/LoReflection_arch_p0').exists() else Path.cwd()
reports={
 'basic_metric_v2': ROOT/'outputs/qwen_arch_incontext_p1_small_metric_v2/eval/p1_small_metric_v2_eval_report.json',
 'llm_functional': ROOT/'outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional/eval/llm_functional_eval_report.json',
 'mixed_llm': ROOT/'outputs/qwen_arch_incontext_p1_small_metric_v2_mixed_llm/eval/mixed_llm_eval_report.json',
}
metrics=['target_pixel_agreement_after_quantization','furniture_pixel_precision','furniture_pixel_recall','furniture_pixel_f1','palette_unknown_rate_after_quantization','uses_context_image','uses_metric_transform','forbidden_inpaint_fields_present']
out=[]
for name,path in reports.items():
    row={'experiment':name,'report':str(path),'exists':path.exists()}
    if path.exists():
        data=json.loads(path.read_text())
        for m in metrics: row[m]=data.get(m)
    out.append(row)
rep=ROOT/'reports/prompt_label_generation'; rep.mkdir(parents=True,exist_ok=True)
(rep/'prompt_source_ablation_summary.json').write_text(json.dumps({'experiments':out},ensure_ascii=False,indent=2)+'\n')
md=['# Prompt Source Ablation Summary','','| experiment | target agreement | precision | recall | furniture F1 | palette unknown | context | metric transform | forbidden old fields |','|---|---:|---:|---:|---:|---:|---|---|---|']
for r in out:
    md.append(f"| {r['experiment']} | {r.get('target_pixel_agreement_after_quantization')} | {r.get('furniture_pixel_precision')} | {r.get('furniture_pixel_recall')} | {r.get('furniture_pixel_f1')} | {r.get('palette_unknown_rate_after_quantization')} | {r.get('uses_context_image')} | {r.get('uses_metric_transform')} | {r.get('forbidden_inpaint_fields_present')} |")
(rep/'PROMPT_SOURCE_ABLATION_SUMMARY.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'experiments':out},ensure_ascii=False,indent=2))
