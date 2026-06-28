from pathlib import Path
import json


def test_p1_small_config_keeps_arch_incontext_contract():
    text = Path('configs/qwen_arch_control/p1_small_full_condition.yaml').read_text(encoding='utf-8')
    assert 'data_file_keys: image,context_image' in text
    assert 'extra_inputs: context_image' in text
    assert 'target_full_semantic' in text


def test_p1_small_dataset_audit_if_present():
    path = Path('data/loreflection_qwen_arch_control_p1_small/audits/dataset_audit_report.json')
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding='utf-8'))
    assert report['num_samples'] >= 200
    assert report['real_source_rate'] == 1.0
    assert report['procedural_source_rate'] == 0.0
    assert report['training_ready'] is True
