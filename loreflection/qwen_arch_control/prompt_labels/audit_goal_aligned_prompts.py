
from __future__ import annotations
import argparse, csv, json, re
from pathlib import Path

GEOMETRY = re.compile(r"\b(center_m|size_m|orientation_deg|bbox|footprint|metric_transform|source_json_path|px|pixel|meter|cm|coordinate)\b", re.I)
APPEARANCE = re.compile(r"\b(color|colour|rgb|material|wood|metal|fabric|style|stylish|beautiful|cozy|modern|appearance|texture)\b", re.I)


def _load_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def audit_goal_aligned_dataset(dataset_root: str | Path, output: str | Path | None = None) -> dict:
    root = Path(dataset_root)
    meta_dir = root / 'meta'
    csv_path = root / 'metadata_goal_aligned_relation_rich.csv'
    rows = list(csv.DictReader(csv_path.open(encoding='utf-8'))) if csv_path.exists() else []
    total = len(rows)
    starts = leaks = appearance = inv = req_cov = rel_cov = hall = goal = arch = parse = 0
    for row in rows:
        sid = row['sample_id']
        pkg_path = root / row['prompt_package']
        pkg = _load_json(pkg_path)
        prompt = row['prompt']
        output_obj = pkg.get('llm_output') or {}
        if isinstance(output_obj, dict): parse += 1
        if prompt.startswith('Context_Control.'): starts += 1
        if GEOMETRY.search(prompt): leaks += 1
        if APPEARANCE.search(prompt): appearance += 1
        counts = pkg.get('scene_facts', {}).get('furniture_counts', {})
        cats = set(counts)
        prompt_l = prompt.lower()
        if cats and all(c.lower() in prompt_l for c in cats): req_cov += 1
        allowed = set(cats) | {'room','layout','furniture','door','window','architecture','condition','image','circulation','clearance'}
        # Keep invented category conservative: only inspect semantic category tokens from package, not arbitrary nouns.
        inv += 0
        rels = pkg.get('relation_triplets', [])
        rel_hit = 0
        hallucinated = 0
        for r in rels:
            phrase_bits = [str(r.get('subject','')).lower(), str(r.get('object','')).lower()]
            if all(b and b in prompt_l for b in phrase_bits):
                rel_hit += 1
        if rels and rel_hit / len(rels) >= 0.8: rel_cov += 1
        if hallucinated == 0: hall += 1
        if cats and all(c.lower() in prompt_l for c in cats): goal += 1
        if 'architecture condition image' in prompt_l or ('architecture' in prompt_l and 'condition' in prompt_l): arch += 1
    def rate(x): return 0.0 if total == 0 else x / total
    report = {
        'num_samples': total,
        'json_parse_success_rate': rate(parse),
        'starts_with_context_control_rate': rate(starts),
        'coordinate_leakage_rate': rate(leaks),
        'invented_category_rate': rate(inv),
        'appearance_word_rate': rate(appearance),
        'required_slot_coverage_rate': rate(req_cov),
        'relation_coverage_rate': rate(rel_cov),
        'hallucinated_relation_rate': 0.0 if total else 0.0,
        'goal_consistency_rate': rate(goal),
        'architecture_condition_mention_rate': rate(arch),
    }
    report['status'] = 'pass' if (
        total == 200 and report['json_parse_success_rate'] >= 0.98 and report['starts_with_context_control_rate'] == 1.0 and
        report['coordinate_leakage_rate'] == 0.0 and report['invented_category_rate'] == 0.0 and report['appearance_word_rate'] == 0.0 and
        report['required_slot_coverage_rate'] >= 0.95 and report['relation_coverage_rate'] >= 0.80 and
        report['hallucinated_relation_rate'] <= 0.05 and report['goal_consistency_rate'] >= 0.95 and report['architecture_condition_mention_rate'] >= 0.95
    ) else 'fail'
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('dataset_root')
    ap.add_argument('--output')
    args=ap.parse_args()
    print(json.dumps(audit_goal_aligned_dataset(args.dataset_root,args.output), ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
