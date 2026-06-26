
import csv, json
from pathlib import Path
from loreflection.qwen_arch_control.prompt_labels.audit_goal_aligned_prompts import audit_goal_aligned_dataset


def test_goal_aligned_prompt_audit_smoke(tmp_path: Path):
    root=tmp_path; (root/'meta').mkdir()
    prompt='Context_Control. Create a bedroom layout with 1 double_bed. Keep double_bed near wardrobe. Follow the architecture condition image and keep circulation clear.'
    pkg={"scene_facts":{"furniture_counts":{"double_bed":1}},"relation_triplets":[{"subject":"double_bed","predicate":"near","object":"wardrobe"}],"llm_output":{"prompt_llm_relation_rich":prompt}}
    (root/'meta/s1_goal_aligned_llm_prompt_package.json').write_text(json.dumps(pkg))
    with (root/'metadata_goal_aligned_relation_rich.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['image','prompt','context_image','sample_id','goal_lostate','prompt_package','verifier_refs']); w.writeheader(); w.writerow({'image':'a.png','prompt':prompt,'context_image':'c.png','sample_id':'s1','goal_lostate':'g.json','prompt_package':'meta/s1_goal_aligned_llm_prompt_package.json','verifier_refs':'v.json'})
    rep=audit_goal_aligned_dataset(root)
    assert rep['num_samples'] == 1
    assert rep['coordinate_leakage_rate'] == 0.0
