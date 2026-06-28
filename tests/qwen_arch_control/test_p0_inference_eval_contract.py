import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from loreflection.semantic_registry import load_registry
from scripts.qwen_arch_control.evaluate_p0_sanity_outputs import evaluate


def test_p0_eval_reports_overfit_success_from_quantized_outputs(tmp_path: Path):
    dataset = tmp_path / "dataset"
    output = tmp_path / "out"
    (dataset / "target").mkdir(parents=True)
    (dataset / "cond").mkdir()
    (output / "infer").mkdir(parents=True)
    (output / "quantized").mkdir()
    (output / "logs").mkdir()

    registry = load_registry()
    object_rgb = registry.id_to_rgb[next(iter(registry.object_ids))]
    arr = np.zeros((4, 4, 3), dtype=np.uint8)
    arr[:, :] = np.array(object_rgb, dtype=np.uint8)
    Image.fromarray(arr).save(dataset / "target/sample_target_semantic.png")
    Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8)).save(dataset / "cond/sample_arch_condition.png")
    Image.fromarray(arr).save(output / "infer/sample_raw.png")
    Image.fromarray(arr).save(output / "quantized/sample_quantized.png")

    metadata = output / "metadata.csv"
    with metadata.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image", "prompt", "context_image", "sample_id"])
        writer.writeheader()
        writer.writerow(
            {
                "image": "target/sample_target_semantic.png",
                "prompt": "Context_Control. draw one bed",
                "context_image": "cond/sample_arch_condition.png",
                "sample_id": "sample",
            }
        )
    (output / "eval").mkdir()
    (output / "eval/palette_quantization_report.json").write_text(
        json.dumps(
            {
                "unknown_color_rate_before_quantization": 0.1,
                "unknown_color_rate_after_quantization": 0.0,
            }
        ),
        encoding="utf-8",
    )
    log = output / "logs/cmd.txt"
    log.write_text(
        '--data_file_keys "image,context_image"\n'
        '--extra_inputs "context_image"\n'
        'Qwen-Image-In-Context-Control-Union\n',
        encoding="utf-8",
    )

    report = evaluate(output, dataset, metadata, [log], [Path("scripts/qwen_arch_control/infer_qwen_arch_incontext.py")])

    assert report["inference_ran"] is True
    assert report["target_pixel_agreement_after_quantization"] == 1.0
    assert report["furniture_pixel_f1"] == 1.0
    assert report["overfit_success"] is True
    assert report["training_command_current_contract_present"] is True
