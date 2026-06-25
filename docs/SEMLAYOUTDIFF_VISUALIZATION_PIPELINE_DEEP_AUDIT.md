# SemLayoutDiff Visualization Pipeline Deep Audit

This report is generated from local SemLayoutDiff source, metadata/config files, explicit external-parser references, and existing processed outputs.

## Completeness
- `source_coverage_complete`: `True`
- `category_mapping_chain_complete`: `True`
- `furniture_rendering_policy_complete`: `True`
- `architecture_rendering_policy_complete`: `True`
- `draw_order_complete`: `True`
- `crop_resize_policy_complete`: `True`

## Call Chain
### raw parser entry
- confidence: `hard evidence`
- file: `preprocess/scripts/pickle_threed_front_dataset.py`
  - L11: `from threed_front.datasets.parse_utils import parse_threed_front_scenes_from_dataset`
  - L43: `scenes = parse_threed_front_scenes_from_dataset(`
- file: `preprocess/scripts/utils/threed_front.py`
  - L19: `from utils import parse_threed_front_scenes`
  - L169: `scenes = parse_threed_front_scenes(`
- file: `preprocess/threed_front/datasets/parse_utils.py`
  - L16: `def parse_threed_front_scenes(`
  - L29: `scenes = parse_threed_front_scenes_from_dataset(`
  - L38: `def parse_threed_front_scenes_from_dataset(`
### room construction
- confidence: `hard evidence`
- file: `configs/apm/chinese_attr_only_55.yaml`
  - L54: `semantic_map_dir: datasets/results/sample_mix_arch_diningroom`
  - L56: `room_type: unified`
  - L60: `room_type: unified`
- file: `configs/apm/chinese_attr_only_inference.yaml`
  - L50: `semantic_map_dir: datasets/results/sample_mix_arch_diningroom`
  - L52: `room_type: unified`
  - L58: `room_type: unified`
- file: `configs/apm/chinese_attr_only_planjson.yaml`
  - L54: `semantic_map_dir: datasets/results/sample_mix_arch_diningroom`
  - L56: `room_type: unified`
  - L60: `room_type: unified`
### furniture construction
- confidence: `hard evidence`
- file: `datasets/chinese_w_arch_3dfront_planjson_apm_stage1_roty_0228_0317_0327_v1/test/1038297_48725/Updated_Bottom_inst_anno.json`
  - L32: `"source_bucket": "furnitureData"`
  - L64: `"source_bucket": "furnitureData"`
  - L96: `"source_bucket": "furnitureData"`
- file: `datasets/chinese_w_arch_3dfront_planjson_apm_stage1_roty_0228_0317_0327_v1/test/1038297_49556/Updated_Bottom_inst_anno.json`
  - L32: `"source_bucket": "furnitureData"`
  - L64: `"source_bucket": "furnitureData"`
  - L96: `"source_bucket": "furnitureData"`
- file: `datasets/chinese_w_arch_3dfront_planjson_apm_stage1_roty_0228_0317_0327_v1/test/1038297_50429/Updated_Bottom_inst_anno.json`
  - L32: `"source_bucket": "furnitureData"`
  - L64: `"source_bucket": "furnitureData"`
  - L96: `"source_bucket": "furnitureData"`
### category mapping
- confidence: `hard evidence`
- file: `configs/apm/chinese_attr_only_55.yaml`
  - L16: `ignore_category_ids: [1, 36, 37]`
- file: `configs/apm/chinese_attr_only_inference.yaml`
  - L13: `ignore_category_ids: [1, 36, 37]`
- file: `configs/apm/chinese_attr_only_planjson.yaml`
  - L16: `ignore_category_ids: [1, 36, 37]`
### geometry extraction
- confidence: `hard evidence`
- file: `checkpoints/apm_attr_only_planjson_stage1_roty_0228_0317_0327_v1/csv_logs/version_3/metrics.csv`
  - L1: `epoch,step,train_offset_loss_epoch,train_offset_loss_step,train_orient_acc_epoch,train_orient_acc_step,train_orient_loss_epoch,train_orient_loss_step,train_size_loss_epoch,train_size_loss_step,train_total_loss_epoch,train_total_loss_step,val_height_mae,val_off`
- file: `checkpoints/apm_attr_only_planjson_stage1_roty_orient0327_v2/csv_logs/version_0/metrics.csv`
  - L1: `epoch,step,train_offset_loss_epoch,train_offset_loss_step,train_orient_acc_epoch,train_orient_acc_step,train_orient_loss_epoch,train_orient_loss_step,train_size_loss_epoch,train_size_loss_step,train_total_loss_epoch,train_total_loss_step,val_height_mae,val_off`
- file: `checkpoints/apm_attr_only_planjson_stage1_roty_orient0327_v2/csv_logs/version_1/metrics.csv`
  - L1: `epoch,step,train_offset_loss_epoch,train_offset_loss_step,train_orient_acc_epoch,train_orient_acc_step,train_orient_loss_epoch,train_orient_loss_step,train_size_loss_epoch,train_size_loss_step,train_total_loss_epoch,train_total_loss_step,val_height_mae,val_off`
### top-down rendering
- confidence: `hard evidence`
- file: `preprocess/README.md`
  - L52: `blenderproc run preprocess/semlayout/render_dataset_improved_mat.py \`
  - L67: `preprocess/semlayout/render_dataset_improved_mat.py \`
- file: `preprocess/metadata/render_orthographic.json`
  - L3: `"type": "orthographic",`
- file: `preprocess/threed_front/simple_3dviz_setup.py`
  - L3: `ORTHOGRAPHIC_PROJECTION_SCENE = {`
### architecture rendering
- confidence: `hard evidence`
- file: `configs/apm/chinese_attr_only_55.yaml`
  - L13: `floor_id: 1`
- file: `configs/apm/chinese_attr_only_inference.yaml`
  - L10: `floor_id: 1`
- file: `configs/apm/chinese_attr_only_planjson.yaml`
  - L13: `floor_id: 1`
### semantic label generation
- confidence: `hard evidence`
- file: `configs/apm/chinese_attr_only_55.yaml`
  - L18: `semantic_encoder:`
  - L54: `semantic_map_dir: datasets/results/sample_mix_arch_diningroom`
- file: `configs/apm/chinese_attr_only_inference.yaml`
  - L15: `semantic_encoder:`
  - L50: `semantic_map_dir: datasets/results/sample_mix_arch_diningroom`
- file: `configs/apm/chinese_attr_only_planjson.yaml`
  - L18: `semantic_encoder:`
  - L54: `semantic_map_dir: datasets/results/sample_mix_arch_diningroom`
### color conversion
- confidence: `hard evidence`
- file: `configs/apm/chinese_attr_only_inference.yaml`
  - L38: `color_palette_path: preprocess/scripts/config/color_palette.json`
- file: `configs/apm/inference_customize.yaml`
  - L48: `# Color palette for visualization`
  - L49: `color_palette_path: preprocess/scripts/config/color_palette.json`
- file: `configs/evaluation_sldn_layout.yaml`
  - L15: `c2rgb_path: my_tools/c2rgb.json`
### instance annotation
- confidence: `hard evidence`
- file: `configs/apm/inference_customize.yaml`
  - L91: `bbox: False`
  - L102: `process_prior_bbox: False`
- file: `configs/apm/unified_config.yaml`
  - L59: `bbox: False`
  - L69: `process_prior_bbox: False`
- file: `configs/data_processing.yaml`
  - L8: `bbox: False`
### crop/resize/padding
- confidence: `hard evidence`
- file: `preprocess/scripts/data_processor.py`
  - L5: `1. First padding images to target size and converting masks to bounding boxes`
  - L144: `# Calculate padding`
- file: `preprocess/scripts/data_to_npy.py`
  - L33: `torchvision.transforms.Resize((H, W), interpolation=0),`
- file: `preprocess/scripts/utils/threed_front.py`
  - L167: `path_to_models, path_to_room_masks_dir=None,`
  - L173: `path_to_room_masks_dir`
  - L213: `def room_mask(self):`
### output writing
- confidence: `hard evidence`
- file: `configs/apm/chinese_attr_only_inference.yaml`
  - L38: `color_palette_path: preprocess/scripts/config/color_palette.json`
- file: `configs/apm/chinese_attr_only_planjson_apm_stage1_roty_0228_0317_0327_v1.yaml`
  - L114: `new_label_to_generic_label_path: preprocess/metadata/apm_stage1_roty_0228_0317_0327_v1/chinese_idx_to_generic_label.json`
  - L115: `pix_ratio_threshold: preprocess/metadata/apm_stage1_roty_0228_0317_0327_v1/chinese_pix_ratio_threshold.json`
- file: `configs/apm/chinese_attr_only_planjson_apm_stage1_roty_orient0327_v1.yaml`
  - L114: `new_label_to_generic_label_path: preprocess/metadata/apm_stage1_roty_orient0327_v1/chinese_idx_to_generic_label.json`
  - L115: `pix_ratio_threshold: preprocess/metadata/apm_stage1_roty_orient0327_v1/chinese_pix_ratio_threshold.json`

## Important Boundary
The user-uploaded `parse_json_floorplan.py` is not treated as SemLayoutDiff official source evidence.

## LoReflection Implication
Phase B may proceed only if all required completeness flags are true. Audit-only legends and labels are LoReflection enhancements, not SemLayoutDiff native behavior unless direct source evidence is found.