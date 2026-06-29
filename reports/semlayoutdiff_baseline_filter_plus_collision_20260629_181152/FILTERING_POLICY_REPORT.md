# Filtering Policy Report

## Scope

Small dry-run audit over `200` raw 3D-FRONT scene JSON files from:

`/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front`

This did not generate training data and did not modify metadata.

## Base Filtering Follows SemLayoutDiff

- `data["furniture"]` contributes to `furniture_by_uid` only when `valid == true`.
- Rooms only consume furniture referenced by the current `room.children` list.
- A furniture child scale with any dimension `< 1e-5` or `> 5` drops the whole room as `semlayoutdiff_invalid_scale`.
- A room must have more than one mapped furniture object to be retained.

## LoReflection Added Clean-Data Sanity Gate

- `hard_footprint_collision_pairs(objects)` is the only extra LoReflection gate enabled here.
- If a severe 2D footprint overlap has `intersection_over_min_area > HARD_FOOTPRINT_COLLISION_MIN_AREA_RATIO`, the whole room is dropped as `hard_footprint_collision`.
- This is not a SemLayoutDiff baseline rule; it is a LoReflection clean-data sanity gate for removing visibly colliding GT rooms.

## Explicitly Not Enabled

- No `inside_floor_ratio` gate.
- No door/window required gate.
- No furniture count upper-bound gate.
- No semantic relationship filtering.
- No door/window visibility gate.
- No strict bbox-outside-floor gate.

## Dry-run Summary

- scenes scanned: 200
- rooms kept: 101
- unsupported room drops: 1236
- invalid scale room drops: 4
- insufficient mapped object drops: 29
- hard collision room drops: 278
- invalid or unmapped furniture count: 54

Top collision pairs:

```json
[
  [
    "double_bed | pendant_lamp",
    85
  ],
  [
    "nightstand | wardrobe",
    66
  ],
  [
    "nightstand | pendant_lamp",
    42
  ],
  [
    "ceiling_lamp | double_bed",
    39
  ],
  [
    "dining_table | pendant_lamp",
    34
  ],
  [
    "coffee_table | pendant_lamp",
    28
  ],
  [
    "dining_chair | dining_table",
    14
  ],
  [
    "pendant_lamp | wardrobe",
    12
  ],
  [
    "wardrobe | wardrobe",
    12
  ],
  [
    "corner_side_table | pendant_lamp",
    9
  ],
  [
    "ceiling_lamp | wardrobe",
    7
  ],
  [
    "ceiling_lamp | kids_bed",
    7
  ],
  [
    "dressing_chair | dressing_table",
    7
  ],
  [
    "pendant_lamp | single_bed",
    7
  ],
  [
    "l_shaped_sofa | pendant_lamp",
    6
  ],
  [
    "dining_chair | dressing_table",
    5
  ],
  [
    "corner_side_table | wardrobe",
    5
  ],
  [
    "ceiling_lamp | single_bed",
    5
  ],
  [
    "cabinet | ceiling_lamp",
    5
  ],
  [
    "double_bed | wardrobe",
    4
  ]
]
```
