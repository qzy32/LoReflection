#!/usr/bin/env bash
set -euo pipefail

# Draft evaluator wrapper. The evaluator must report architecture and furniture
# metrics separately because full-image agreement can hide furniture errors.
REPO_ROOT=${REPO_ROOT:-/wuqingyaoa800/qiuziyan/LoReflection_arch_p0}
DATASET_ROOT=${DATASET_ROOT:-$REPO_ROOT/data/loreflection_qwen_arch_control_p1_small_metric_v2_full_semantic_target}
METADATA=${METADATA:-$DATASET_ROOT/metadata_llm_functional_full_semantic_target.csv}
OUT=${OUT:-$REPO_ROOT/outputs/qwen_arch_incontext_p1_small_metric_v2_llm_functional_full_semantic_target}

python "$REPO_ROOT/scripts/qwen_arch_control/quantize_qwen_output_palette.py" \
  --input-dir "$OUT/infer" \
  --output-dir "$OUT/quantized" \
  --report "$OUT/eval/palette_quantization_report.json"

python "$REPO_ROOT/scripts/qwen_arch_control/evaluate_p0_sanity_outputs.py" \
  --dataset-root "$DATASET_ROOT" \
  --metadata "$METADATA" \
  --outputs-root "$OUT" \
  --report "$OUT/eval/full_semantic_target_eval_report.json"

cat > "$OUT/eval/FULL_SEMANTIC_EVAL_NOTE.md" <<'EOF'
# Full Semantic Evaluation Note

This draft route must report these metrics before it can be used for decisions:

- full_image_pixel_agreement
- architecture_preservation_accuracy
- furniture_pixel_precision
- furniture_pixel_recall
- furniture_pixel_f1
- furniture_class_color_accuracy
- forbidden_architecture_overwrite_rate
- palette_unknown_rate_before_quantization
- palette_unknown_rate_after_quantization

Current furniture-only evaluators are insufficient if they collapse this into
one full-image pixel score.
EOF
