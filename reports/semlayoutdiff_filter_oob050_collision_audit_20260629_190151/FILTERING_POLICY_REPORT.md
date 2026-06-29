# Filtering Policy Report - OOB 0.50 + Collision Audit Only

- scenes scanned: 200
- rooms kept: 373
- unsupported room drops: 1236
- invalid scale drops: 4
- insufficient mapped object drops: 29
- severe_oob_footprint drops: 6
- center_outside_boundary_bbox audit count: 1
- inter-object collision room drops: 0
- severe OOB threshold: 0.5

Inter-object collision remains audit-only. Center outside bbox is audit-only and does not independently drop a room.

## Top inter-object collision pairs, audit-only

```json
[
  [
    "nightstand | wardrobe",
    66
  ],
  [
    "dining_chair | dining_table",
    14
  ],
  [
    "wardrobe | wardrobe",
    12
  ],
  [
    "dressing_chair | dressing_table",
    7
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
    "double_bed | wardrobe",
    4
  ],
  [
    "corner_side_table | desk",
    4
  ],
  [
    "desk | stool",
    4
  ],
  [
    "dining_chair | wardrobe",
    4
  ],
  [
    "cabinet | stool",
    4
  ],
  [
    "corner_side_table | multi_seat_sofa",
    3
  ],
  [
    "desk | desk",
    3
  ],
  [
    "cabinet | wardrobe",
    3
  ],
  [
    "stool | wardrobe",
    3
  ],
  [
    "corner_side_table | dining_table",
    2
  ],
  [
    "desk | dining_table",
    2
  ],
  [
    "desk | lounge_chair",
    2
  ],
  [
    "corner_side_table | double_bed",
    2
  ],
  [
    "coffee_table | wardrobe",
    2
  ]
]
```

## Top severe OOB categories

```json
[
  [
    "wardrobe",
    4
  ],
  [
    "bookshelf",
    2
  ]
]
```