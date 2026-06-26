
from loreflection.qwen_arch_control.prompt_labels.relation_triplet_extractor import extract_relation_triplets


def test_relation_triplet_extractor_keeps_high_confidence_relations():
    layout={"objects":[{"category":"dining_table","center_m":[0,0]},{"category":"dining_chair","center_m":[0.4,0.2]},{"category":"coffee_table","center_m":[2.0,0.1]}]}
    rels=extract_relation_triplets(layout, {}, {}, {"primary_anchor":"dining_table"})
    assert 2 <= len(rels) <= 5
    assert any(r["predicate"] in {"near","closely_near","paired_with"} for r in rels)
