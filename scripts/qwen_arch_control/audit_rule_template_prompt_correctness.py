from __future__ import annotations

import argparse
import json
from pathlib import Path

from loreflection.qwen_arch_control.prompt_labels.audit_rule_template_prompt_correctness import audit_rule_template_prompt_correctness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--dataset-base", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = audit_rule_template_prompt_correctness(args.metadata, args.dataset_base)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
