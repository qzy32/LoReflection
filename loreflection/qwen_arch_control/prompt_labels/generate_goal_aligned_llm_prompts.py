
from __future__ import annotations
import argparse, csv, json, re, shutil
from pathlib import Path

from .relation_triplet_extractor import extract_relation_triplets
from .placement_order_planner import plan_placement_order
from .goal_aligned_llm_request_builder import build_goal_aligned_llm_request, deterministic_goal_aligned_output
from .audit_goal_aligned_prompts import audit_goal_aligned_dataset, GEOMETRY, APPEARANCE


def load_json(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def extract_json_object(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None

def valid_prompt(prompt: str, cats: set[str], rels: list[dict]) -> bool:
    low=prompt.lower()
    return prompt.startswith('Context_Control.') and not GEOMETRY.search(prompt) and not APPEARANCE.search(prompt) and all(c.lower() in low for c in cats)

def build_model(model_path: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    tok=AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model=AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.bfloat16, device_map='auto', trust_remote_code=True)
    model.eval()
    return tok, model

def call_llm(tok, model, request: dict) -> dict | None:
    import torch
    messages=[{'role':'system','content':request['system']},{'role':'user','content':json.dumps({'input':request['user'],'required_output_schema':request['required_output_schema']},ensure_ascii=False)}]
    text=tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs=tok([text], return_tensors='pt').to(model.device)
    with torch.no_grad():
        out=model.generate(**inputs, max_new_tokens=300, do_sample=False)
    gen=tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return extract_json_object(gen)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--metric-root', default='data/loreflection_qwen_arch_control_p1_small_metric_v2')
    ap.add_argument('--prompt-label-root', default='data/loreflection_qwen_arch_control_p1_small_metric_v2_prompt_labels')
    ap.add_argument('--output-root', default='data/loreflection_qwen_arch_control_p1_small_metric_v2_goal_aligned_llm_prompts')
    ap.add_argument('--model-path', default='/wuqingyaoa800/chengjiajia_datas/models/Qwen2.5-7B-Instruct')
    ap.add_argument('--num-samples', type=int, default=200)
    ap.add_argument('--no-llm', action='store_true')
    args=ap.parse_args()
    metric=Path(args.metric_root); labels=Path(args.prompt_label_root); out=Path(args.output_root)
    for d in ['cond','target','meta','audits']:(out/d).mkdir(parents=True, exist_ok=True)
    rows=list(csv.DictReader((metric/'metadata.csv').open(encoding='utf-8')))[:args.num_samples]
    tok=model=None
    llm_used=False
    if not args.no_llm:
        tok,model=build_model(args.model_path); llm_used=True
    md_func=[]; md_rel=[]; md_mix=[]
    fallback_count=0; generated_count=0
    for row in rows:
        sid=row['sample_id']
        layout=load_json(metric/'meta'/f'{sid}_layout.json')
        arch=load_json(metric/'meta'/f'{sid}_architecture.json')
        scene_facts=load_json(labels/'meta'/f'{sid}_scene_facts.json')
        rich=load_json(labels/'meta'/f'{sid}_goal_lostate_rich.json')
        rels=extract_relation_triplets(layout, arch, rich, scene_facts, max_triplets=5)
        order=plan_placement_order(scene_facts, rich, rels)
        req=build_goal_aligned_llm_request(scene_facts, rich, rels, order)
        det=deterministic_goal_aligned_output(scene_facts, rels, order)
        obj=None
        if llm_used:
            try: obj=call_llm(tok, model, req)
            except Exception as e: obj={'error':str(e)}
        cats=set(scene_facts.get('furniture_counts',{}))
        if not isinstance(obj, dict) or not valid_prompt(str(obj.get('prompt_llm_relation_rich','')), cats, rels) or not valid_prompt(str(obj.get('prompt_llm_functional','')), cats, rels):
            obj=det; fallback_count += 1
        else:
            generated_count += 1
        pkg={'schema_version':'goal-aligned-llm-prompt-package-v1','sample_id':sid,'scene_facts':scene_facts,'goal_lostate_rich_without_geometry':req['user']['goal_lostate_rich_without_geometry'],'relation_triplets':rels,'placement_order':order,'llm_request':req,'llm_output':obj,'llm_model':args.model_path,'llm_actual_generation_used':llm_used}
        for name,data in [('relation_triplets',rels),('placement_order',order),('goal_aligned_llm_prompt_package',pkg)]:
            write_json(out/'meta'/f'{sid}_{name}.json', data)
        # Copy train assets and required refs into output package.
        for rel in [row['image'], row['context_image']]:
            src=metric/rel; dst=out/rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src,dst)
        for suffix in ['architecture.json','layout.json','verifier_refs.json']:
            src=metric/'meta'/f'{sid}_{suffix}'; dst=out/'meta'/f'{sid}_{suffix}'; shutil.copy2(src,dst)
        shutil.copy2(labels/'meta'/f'{sid}_goal_lostate_rich.json', out/'meta'/f'{sid}_goal_lostate_rich.json')
        common={'image':row['image'],'context_image':row['context_image'],'sample_id':sid,'goal_lostate':f'meta/{sid}_goal_lostate_rich.json','prompt_package':f'meta/{sid}_goal_aligned_llm_prompt_package.json','verifier_refs':f'meta/{sid}_verifier_refs.json'}
        md_func.append({**common,'prompt':obj['prompt_llm_functional']})
        md_rel.append({**common,'prompt':obj['prompt_llm_relation_rich']})
        md_mix.append({**common,'prompt':obj['prompt_llm_functional'] if len(md_mix)%2==0 else obj['prompt_llm_relation_rich']})
    fields=['image','prompt','context_image','sample_id','goal_lostate','prompt_package','verifier_refs']
    for name,rows_out in [('metadata_goal_aligned_llm_functional.csv',md_func),('metadata_goal_aligned_relation_rich.csv',md_rel),('metadata_mixed_goal_aligned_llm_variants.csv',md_mix)]:
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows_out)
    report=audit_goal_aligned_dataset(out, out/'audits/goal_aligned_llm_prompt_audit_report.json')
    report.update({'llm_actual_generation_used':llm_used,'llm_generated_count':generated_count,'fallback_count':fallback_count,'model_path':args.model_path})
    write_json(out/'audits/goal_aligned_llm_prompt_audit_report.json', report)
    rep=Path('reports/prompt_label_generation'); rep.mkdir(parents=True, exist_ok=True)
    write_json(rep/'goal_aligned_llm_prompt_audit_report.json', report)
    examples=[]
    for r in md_rel[:5]: examples.append(f"## {r['sample_id']}\n\n{r['prompt']}\n")
    (rep/'GOAL_ALIGNED_LLM_PROMPT_EXAMPLES.md').write_text('# Goal-aligned LLM Prompt Examples\n\n'+'\n'.join(examples),encoding='utf-8')
    summary=f"""# Goal-aligned LLM Prompt Summary

- dataset: `{out}`
- model: `{args.model_path}`
- num_samples: `{report['num_samples']}`
- llm_actual_generation_used: `{llm_used}`
- llm_generated_count: `{generated_count}`
- fallback_count: `{fallback_count}`
- starts_with_context_control_rate: `{report['starts_with_context_control_rate']}`
- coordinate_leakage_rate: `{report['coordinate_leakage_rate']}`
- invented_category_rate: `{report['invented_category_rate']}`
- appearance_word_rate: `{report['appearance_word_rate']}`
- required_slot_coverage_rate: `{report['required_slot_coverage_rate']}`
- relation_coverage_rate: `{report['relation_coverage_rate']}`
- architecture_condition_mention_rate: `{report['architecture_condition_mention_rate']}`
- status: `{report['status']}`
"""
    (rep/'GOAL_ALIGNED_LLM_PROMPT_SUMMARY.md').write_text(summary,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
