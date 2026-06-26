from __future__ import annotations

import argparse
import json
from pathlib import Path

from loreflection.qwen_arch_control.prompt_labels.audit_palette_contract import audit_metadata_palette_contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--dataset-base", required=True)
    parser.add_argument("--prediction-dir")
    parser.add_argument("--quantized-dir")
    parser.add_argument("--output", required=True)
    parser.add_argument("--matrix-output")
    args = parser.parse_args()
    report = audit_metadata_palette_contract(args.metadata, args.dataset_base, args.prediction_dir, args.quantized_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.matrix_output:
        matrix = report.get("confusion_matrix", {})
        Path(args.matrix_output).write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
