# Metric Transform Audit

## Current Answer

- Qwen input image resolution: `256x256` in the current metric_v2 baseline contract.
- The images are still fixed-size tensors, but real scale is preserved by `architecture.metric_transform`, not by image dimensions alone.
- Previous metric_v2 audit result:
  - `metric_transform_exists_rate = 1.0`
  - `roundtrip_error_p95_m = 0.01956249497439548`
  - `area_consistency_error_p95 = 0.014661426519215742`
  - `target_bbox_fallback_rate = 0.0`

## Scale Interpretation

For the default fixed metric canvas, 8m maps to 256px, so 1m is usually 32px and 1px is 0.03125m. If a room exceeds the 8m bucket, the transform can use a larger canvas extent and a different pixels-per-meter. The exact per-sample values must be read from each sample's `architecture.metric_transform`.

## Local Limitation

This local snapshot does not include the server P1 metric_v2 dataset, so this report records the known committed audit values and adds a script for recomputing the audit on the server dataset.
