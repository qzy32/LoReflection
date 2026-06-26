from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from loreflection.qwen_arch_control.prompt_labels.prompt_compiler_v2 import compile_prompt_package_v2


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compile_metadata(metadata_path: Path, dataset_base: Path, output_path: Path, c2rgb_path: Path, id2c_path: Path | None = None) -> dict:
    rows = list(csv.DictReader(metadata_path.open(encoding="utf-8"))) if metadata_path.exists() else []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_rows = []
    for idx, row in enumerate(rows):
        goal_path = dataset_base / row["goal_lostate"]
        pkg_path = dataset_base / row["prompt_package"]
        goal = _load(goal_path)
        pkg = _load(pkg_path)
        compiled = compile_prompt_package_v2(
            user_intent_prompt=row["prompt"],
            goal_lostate=goal,
            prompt_package=pkg,
            c2rgb_path=c2rgb_path,
            id2c_path=id2c_path,
            source_prompt_package=row["prompt_package"],
            goal_lostate_ref=row["goal_lostate"],
        )
        variant = pkg.get("variant_name") or pkg.get("prompt_source") or "prompt"
        compiled_rel = f"meta/{row['sample_id']}_row{idx:06d}_{variant}_compiled_palette_prompt_package.json"
        compiled_path = dataset_base / compiled_rel
        compiled_path.parent.mkdir(parents=True, exist_ok=True)
        compiled_path.write_text(json.dumps(compiled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        new_row = dict(row)
        new_row["prompt"] = compiled["compiled_prompt"]
        new_row["prompt_package"] = compiled_rel
        out_rows.append(new_row)
    if rows:
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
            writer.writeheader()
            writer.writerows(out_rows)
    return {"input": metadata_path.as_posix(), "output": output_path.as_posix(), "num_rows": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--dataset-base", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--c2rgb", default="artifacts/semantic_registry_v2/palette_frozen.json")
    parser.add_argument("--id2c")
    args = parser.parse_args()
    report = compile_metadata(Path(args.metadata), Path(args.dataset_base), Path(args.output), Path(args.c2rgb), Path(args.id2c) if args.id2c else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
