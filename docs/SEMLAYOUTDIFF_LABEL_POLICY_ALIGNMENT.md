# SemLayoutDiff Label Policy Alignment

## Purpose

Step 3.2B-R repaired geometry and transform extraction, but non-core object
policy still needs to be aligned with the reference SemLayoutDiff preprocessing
pipeline. In particular, doors and windows should not be furniture entities,
but they should not disappear: they are architecture-condition evidence.

## Policy Questions

The alignment inspector checks:

- Whether architecture / condition maps include wall, door, window, opening,
  floor, background, or room-boundary labels.
- Which furniture semantic classes are present in SemLayoutDiff metadata.
- Whether door, window, curtain, and lamp are treated as architecture
  condition, furniture labels, accessory labels, ignored objects, or unknown.
- Whether processed `Updated_Bottom_label_map.png` and
  `Updated_Bottom_inst_anno.json` are furniture-only, architecture-only, mixed,
  or unclear.

## LoReflection Intended Policy

- Door/window/opening/wall/floor/background are architecture condition or
  Architecture JSON anchor concepts, not furniture entities.
- Core furniture remains the current LoReflection palette:
  bed, wardrobe, desk, chair, nightstand.
- Curtains, lamps, plants, pillows, and decor remain accessory-or-ignore unless
  the palette is explicitly expanded.
- All parsed objects keep raw category, reference category, and LoReflection
  category fields during diagnostics.
- SemLayoutDiff processed label maps may be used as policy/reference
  visualization, not as raw geometry source.

## Converter Updates For R2

Before the next core-filtered rerun:

1. Move door/window-like objects out of Observed LoState furniture instances.
2. Store them as Architecture JSON anchors with source JID, raw title/category,
   transform source, and footprint candidate when available.
3. Render door/window anchors in the architecture condition image.
4. Keep semantic furniture layout limited to core furniture classes.
5. Report accessory/ignored counts separately from unknown mapping failures.

## Required User Decisions

- Whether curtain should be treated as architecture-covering anchor or ignored.
- Whether lamp should become an optional semantic class later.
- Whether sofa/table/cabinet should be folded into the five current palette
  classes or require palette expansion before val50.
