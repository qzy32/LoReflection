# Filtering Policy Report - Severe OOB Only

## Change

- SemLayoutDiff baseline remains: valid furniture, room.children only, invalid scale drops room, mapped objects >= 2.
- LoReflection extra hard drop is now only `severe_oob_footprint`.
- Inter-object footprint collision is audit-only and never drops a room.
- OOB first version uses the current room boundary bbox with outside area ratio threshold `0.2`; it is not an exact wall-collision polygon test.

## 200 Scene Audit

- scenes scanned: 200
- rooms kept: 137
- severe OOB dropped rooms: 242
- inter-object collision room drops: 0
- invalid scale dropped rooms: 4

## Top Inter-object Collision Pairs, Audit Only

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

## Top Severe OOB Categories

```json
[
  [
    "wardrobe",
    149
  ],
  [
    "nightstand",
    88
  ],
  [
    "cabinet",
    50
  ],
  [
    "bookshelf",
    33
  ],
  [
    "dressing_table",
    27
  ],
  [
    "desk",
    12
  ],
  [
    "pendant_lamp",
    11
  ],
  [
    "children_cabinet",
    8
  ],
  [
    "tv_stand",
    7
  ],
  [
    "corner_side_table",
    6
  ],
  [
    "shelf",
    6
  ],
  [
    "wine_cabinet",
    5
  ],
  [
    "stool",
    2
  ],
  [
    "round_end_table",
    1
  ],
  [
    "kids_bed",
    1
  ],
  [
    "dining_table",
    1
  ]
]
```
