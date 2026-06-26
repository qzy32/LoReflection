#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export QWEN_SOURCE_MODE="${QWEN_SOURCE_MODE:-raw_3dfront}"
export QWEN_3DFRONT_ROOT="${QWEN_3DFRONT_ROOT:-/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front}"
export QWEN_OUTPUT_ROOT="${QWEN_OUTPUT_ROOT:-data/loreflection_qwen_arch_control_p1_small}"
export P1_NUM_SAMPLES="${P1_NUM_SAMPLES:-200}"
export P1_IMAGE_SIZE="${P1_IMAGE_SIZE:-256}"
export P1_SEED="${P1_SEED:-5521}"
export PYTHON_BIN="${PYTHON_BIN:-/home/chengjiajia/anaconda3/bin/python}"
mkdir -p "$QWEN_OUTPUT_ROOT/audits" reports/p1_small
"$PYTHON_BIN" -m loreflection.qwen_arch_control.build_qwen_arch_control_dataset \
  --source-mode "$QWEN_SOURCE_MODE" \
  --data-root "$QWEN_3DFRONT_ROOT" \
  --output-root "$QWEN_OUTPUT_ROOT" \
  --num-samples "$P1_NUM_SAMPLES" \
  --image-size "$P1_IMAGE_SIZE" \
  --seed "$P1_SEED"
"$PYTHON_BIN" tools/validate_arch_incontext_training_metadata.py \
  "$QWEN_OUTPUT_ROOT/metadata.csv" \
  --dataset-base "$QWEN_OUTPUT_ROOT" \
  --output "$QWEN_OUTPUT_ROOT/audits/metadata_validator_report.json"
"$PYTHON_BIN" -m loreflection.qwen_arch_control.audit_palette_exact "$QWEN_OUTPUT_ROOT"
"$PYTHON_BIN" -m loreflection.qwen_arch_control.audit_prompt_no_coordinate_leakage "$QWEN_OUTPUT_ROOT"
"$PYTHON_BIN" -m loreflection.qwen_arch_control.audit_qwen_arch_control_dataset "$QWEN_OUTPUT_ROOT"
"$PYTHON_BIN" -m loreflection.qwen_arch_control.preview_qwen_arch_dataset "$QWEN_OUTPUT_ROOT"
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import csv, json, collections
root = Path('data/loreflection_qwen_arch_control_p1_small')
aud = json.loads((root/'audits/dataset_audit_report.json').read_text())
pal = json.loads((root/'audits/palette_audit_report.json').read_text())
leak = json.loads((root/'audits/prompt_leakage_report.json').read_text())
build = json.loads((root/'audits/p0_build_result.json').read_text()) if (root/'audits/p0_build_result.json').exists() else {}
rows = list(csv.DictReader((root/'metadata.csv').open(encoding='utf-8')))
rooms = collections.Counter()
for r in rows:
    sid = r.get('sample_id','')
    mf = root/'meta'/f'{sid}_sample_manifest.json'
    if mf.exists():
        obj = json.loads(mf.read_text())
        rooms[str(obj.get('room_type','unknown'))] += 1
summary = f'''# P1-small Dataset Summary\n\n- dataset_path: `{root}`\n- sample_count: `{len(rows)}`\n- training_ready: `{aud.get('training_ready')}`\n- source_mode: `{aud.get('source_mode')}`\n- real_source_rate: `{aud.get('real_source_rate')}`\n- procedural_source_rate: `{aud.get('procedural_source_rate')}`\n- condition_contains_furniture_rate: `{aud.get('condition_contains_furniture_rate')}`\n- target_has_furniture_pixels_rate: `{aud.get('target_has_furniture_pixels_rate')}`\n- prompt_coordinate_leakage_rate: `{aud.get('prompt_coordinate_leakage_rate')}`\n- train_val_test_scene_leakage_rate: `{aud.get('train_val_test_scene_leakage_rate')}`\n- palette_condition_unknown_rate: `{pal.get('condition_palette_unknown_rate')}`\n- palette_target_unknown_rate: `{pal.get('target_palette_unknown_rate')}`\n- prompt_leakage_status: `{leak.get('status')}`\n- preview_html: `{root/'previews/index.html'}`\n- preview_contact_sheet: `{root/'previews/contact_sheet.png'}`\n\n## Room Type Distribution\n\n```json\n{json.dumps(dict(rooms), ensure_ascii=False, indent=2)}\n```\n\n## Build/Audit Files\n\n- dataset_audit: `{root/'audits/dataset_audit_report.json'}`\n- palette_audit: `{root/'audits/palette_audit_report.json'}`\n- prompt_leakage: `{root/'audits/prompt_leakage_report.json'}`\n- metadata_validator: `{root/'audits/metadata_validator_report.json'}`\n'''
Path('reports/p1_small').mkdir(parents=True, exist_ok=True)
Path('reports/p1_small/P1_SMALL_DATASET_SUMMARY.md').write_text(summary, encoding='utf-8')
print(summary)
PY
