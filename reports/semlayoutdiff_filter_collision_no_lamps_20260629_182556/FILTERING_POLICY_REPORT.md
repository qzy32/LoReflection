# Filtering Policy Report - Lamps Excluded From Hard Collision

## Change

- `pendant_lamp` and `ceiling_lamp` remain semantic objects.
- They are excluded only from `hard_footprint_collision_pairs` because ceiling/pendant lamps are non-blocking for floor footprint collisions.

## 200 Scene Audit

- scenes scanned: 200
- rooms kept: 252 (previous comparable audit: 101)
- hard collision dropped rooms: 127 (previous comparable audit: 278)
- invalid scale dropped rooms: 4
- lamp collision pairs present after filter: False

## Top Collision Pairs

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
