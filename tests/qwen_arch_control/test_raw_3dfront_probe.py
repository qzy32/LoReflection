from loreflection.qwen_arch_control.source_resolver import probe_data_root


def test_probe_finds_scene_and_model_info(tiny_raw_3dfront_root):
    report = probe_data_root(tiny_raw_3dfront_root)
    assert report["scene_json_count"] == 1
    assert len(report["model_info_paths"]) == 1
    assert report["recommended_source_mode"] == "raw_3dfront"
