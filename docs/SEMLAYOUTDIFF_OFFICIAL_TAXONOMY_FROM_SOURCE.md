# SemLayoutDiff Official Taxonomy From Source

- checkout: `/wuqingyaoa800/qiuziyan/third_party_sources/checkouts/SemLayoutDiff_official_6b12bc4c42aa`
- commit: `6b12bc4c42aa8377445af108093539073f0495c1`
- evidence: SemLayoutDiff official checkout metadata/scripts only
- forbidden evidence: parse_json_floorplan.py / Chinese PlanJSON compact taxonomy / 13-class prototype

- total semantic categories: 38
- object categories: 34
- void/floor/door/window IDs: 0 void, 1 floor, 36 door, 37 window
- native palette duplicate RGB groups: 1

| semantic_id | category_name | role | source_file | native_RGB |
|---:|---|---|---|---|
| 0 | void | void | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [255, 255, 255] |
| 1 | floor | floor | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [211, 211, 211] |
| 2 | kids_bed | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [152, 223, 138] |
| 3 | single_bed | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [105, 183, 100] |
| 4 | double_bed | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [44, 160, 44] |
| 5 | corner_side_table | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [197, 176, 213] |
| 6 | round_end_table | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [187, 166, 212] |
| 7 | coffee_table | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [178, 157, 212] |
| 8 | console_table | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [169, 148, 211] |
| 9 | tv_stand | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [160, 139, 211] |
| 10 | desk | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [150, 129, 211] |
| 11 | dressing_table | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [141, 120, 210] |
| 12 | table | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [132, 111, 210] |
| 13 | dining_table | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [123, 102, 210] |
| 14 | stool | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [23, 190, 207] |
| 15 | dressing_chair | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [162, 200, 236] |
| 16 | dining_chair | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [151, 193, 231] |
| 17 | chinese_chair | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [140, 186, 226] |
| 18 | armchair | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [74, 146, 198] |
| 19 | chair | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [52, 132, 189] |
| 20 | lounge_chair | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [31, 119, 180] |
| 21 | loveseat_sofa | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [243, 171, 207] |
| 22 | lazy_sofa | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [241, 166, 205] |
| 23 | sofa | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [240, 161, 204] |
| 24 | multi_seat_sofa | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [241, 166, 205] |
| 25 | chaise_longue_sofa | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [233, 140, 199] |
| 26 | l_shaped_sofa | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [227, 119, 194] |
| 27 | nightstand | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [255, 217, 74] |
| 28 | shelf | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [215, 216, 130] |
| 29 | bookshelf | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [212, 213, 119] |
| 30 | children_cabinet | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [206, 207, 98] |
| 31 | wine_cabinet | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [200, 201, 76] |
| 32 | cabinet | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [194, 195, 55] |
| 33 | wardrobe | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [188, 189, 34] |
| 34 | pendant_lamp | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [255, 187, 120] |
| 35 | ceiling_lamp | object | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [255, 127, 14] |
| 36 | door | architecture | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [153, 0, 0] |
| 37 | window | architecture | preprocess/metadata/unified_idx_to_generic_label_w_arch.json | [255, 153, 153] |
