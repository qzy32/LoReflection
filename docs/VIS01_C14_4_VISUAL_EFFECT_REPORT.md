# VIS-01 C14.4 Visual Effect Report

## 1. What C14.4 Completed

C13 was a 3/action small overfit proof. C14.4 is different: it is the first palette-fixed 20/action medium clean diagnostic training run under the corrected evaluator/data/palette contract.

C14.4 trained ADD, REMOVE, TRANSLATE, and REPLACE for 300 steps each, then trained and evaluated MIXED_80. The current conclusion is PARTIAL: REMOVE is the best action with edit_success 0.60 on sampled evaluation, while REPLACE, TRANSLATE, ADD, and MIXED_80 have nonzero learning signal but strict edit_success 0.

![four-action overview](C:/Users/紫燕/Desktop/LoReflection/outputs/manual_review/vis01_c14_4_effect_report/c14_4_four_action_overview.png)

## 2. Four-Action Metrics

|action|rows|steps|loss|masked_accuracy|action_iou|edit_success|gate|main_failure|
|---|---|---|---|---|---|---|---|---|
|REMOVE|20|300|0.0005|0.9138|0.9138|0.6000|CLEAN_ACTION_PARTIAL|strict pass on 3/5 sampled eval; failures still extra components/allowed labels|
|REPLACE|20|300|0.0017|0.4784|0.6109|0.0000|CLEAN_ACTION_PARTIAL|nonzero IoU but strict gate blocked by reconstruction, extra components, or allowed labels|
|TRANSLATE|20|300|0.0021|0.7920|0.6830|0.0000|CLEAN_ACTION_PARTIAL|nonzero IoU but strict gate blocked by reconstruction, extra components, or allowed labels|
|ADD|20|300|0.0025|0.6374|0.8059|0.0000|CLEAN_ACTION_PARTIAL|nonzero IoU but strict gate blocked by reconstruction, extra components, or allowed labels|
|MIXED_80|80|300|0.0025|0.5016|0.8000|0.0000|CLEAN_ACTION_PARTIAL|sampled visual eval currently covers ADD rows only; strict edit_success remains 0|

## 3. How to Read the Visualizations

- I_bad: the bad input image the model receives as condition.
- I_target: the target image we hope the repair should become.
- control_mask: white means the model is allowed to repaint; black means preserve.
- raw_output: direct model output before palette snapping.
- snapped_output: raw output after colors are snapped to the frozen semantic palette.
- copyback_output: snapped pixels inside the mask copied onto I_bad, while black-mask regions are restored from I_bad.
- sanitized_output: this C14.4 evaluator does not emit a separate file; copyback_output is the final constrained output.
- diff_map: red marks where copyback_output differs from I_target.

For REMOVE, first check whether the source object is cleared. For REPLACE, check whether the source disappears and the target appears. For TRANSLATE, check whether old_region is cleared and new_region is generated. For ADD, check whether the target appears completely. If action_iou is high but edit_success is low, inspect extra_component_count and allowed_label_violation_count.

## 4. REMOVE Visual Summary

REMOVE often succeeds: three of five sampled step-300 rows pass strict edit_success. Failures still show extra components or allowed-label violations even when the source object is cleared.

Open: `outputs/manual_review/vis01_c14_4_effect_report/REMOVE`

## 5. REPLACE Visual Summary

REPLACE has nonzero target/action IoU but strict edit_success remains 0. Some rows remove the source and approximate the target, but allowed-label violations, extra components, or low masked reconstruction keep the strict gate closed.

Open: `outputs/manual_review/vis01_c14_4_effect_report/REPLACE`

## 6. TRANSLATE Visual Summary

TRANSLATE mostly preserves black-mask regions and often clears the old region, but new_region target generation is unstable. This is why several samples look half-right while edit_success remains 0.

Open: `outputs/manual_review/vis01_c14_4_effect_report/TRANSLATE`

## 7. ADD Visual Summary

ADD can produce target-like regions with high action_iou on some samples, but target completeness and extra fragments remain unstable. This explains high action_iou with edit_success 0.

Open: `outputs/manual_review/vis01_c14_4_effect_report/ADD`

## 8. MIXED_80 Visual Summary

MIXED_80 was trained and evaluated. The existing sampled visual folder contains ADD rows only because the evaluator used the first five rows of metadata_mixed_80. Treat the mixed visual page as a limited sampled view, not per-action mixed coverage.

![mixed overview](C:/Users/紫燕/Desktop/LoReflection/outputs/manual_review/vis01_c14_4_effect_report/c14_4_mixed_overview.png)

## 9. Failure Examples

![failure examples](C:/Users/紫燕/Desktop/LoReflection/outputs/manual_review/vis01_c14_4_effect_report/c14_4_four_action_failure_examples.png)

## 10. Conclusion

C14.4 proves the training chain and model learning signal are real under the corrected palette contract. It is not ready for 50/action or larger semantic_repair4 training. The next step is C15 action-specific diagnosis: checkpoint A/B, prompt ablation, mask ablation, and allowed-label / extra-component diagnosis.
