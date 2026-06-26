# Server 3D-FRONT Data Probe

Probe date: 2026-06-26

Server: Pazhou A800

Data root:

```text
/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front
```

## Result

The data root exists and contains an extracted 3D-FRONT / 3D-FUTURE bundle.
It is suitable for a bounded raw-data P0 conversion.

## Directory Structure

Important entries:

```text
3D-FRONT/                    extracted scene JSON directory
3D-FRONT.zip                 source archive
3D-FRONT-texture/            extracted texture directory
3D-FRONT-texture.zip
3D-FUTURE-model-part1/
3D-FUTURE-model-part2/
3D-FUTURE-model-part3/
3D-FUTURE-model-part4/
3D-FUTURE-model-part*.zip
```

The complete root occupies approximately 70 GB.

## Scene JSON

Scene directory:

```text
/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front/3D-FRONT
```

Counts:

```text
scene JSON files: 6813
all JSON files below DATA_ROOT: 6819
zip files: 7
```

Twenty scene JSON files were selected with deterministic random seed `4411`.
All 20 parsed successfully.

Common top-level keys:

```text
uid
design_version
code_version
north_vector
furniture
mesh
material
extension
scene
version
jobid
lights
groups
materialList
```

## 3D-FUTURE Metadata

Four extracted `model_info.json` files were found:

```text
3D-FUTURE-model-part1/model_info.json
3D-FUTURE-model-part2/model_info.json
3D-FUTURE-model-part3/model_info.json
3D-FUTURE-model-part4/model_info.json
```

Each file reports 16,563 entries. The files contain repeated global model
metadata, so the adapter merges entries by `model_id` rather than treating the
four files as disjoint category tables.

Observed model metadata fields include:

```text
model_id
category
super-category
style
```

Example categories include `armchair`, `Coffee Table`, `Pendant Lamp`, and
`Lounge Chair / Cafe Chair / Office Chair`.

## Scene Field Structure

All 20 sampled scenes contained:

```text
scene
furniture
mesh
scene.room
room.children
pos
rot
scale
jid
uid
ref
instanceid
```

Typical `scene` keys:

```text
boundingBox
pos
ref
room
rot
scale
```

Typical room keys:

```text
children
empty
instanceid
pos
rot
scale
size
type
```

Typical room-child keys:

```text
instanceid
pos
ref
rot
scale
componentModifiers
components
```

Typical furniture keys:

```text
aid
bbox
jid
size
sourceCategoryId
title
type
uid
valid
```

Room children link to furniture and mesh records through `child.ref`.
Furniture transforms are stored on the room child. A checked room contained
linked furniture plus a `Floor` mesh and a `Window` mesh. Floor mesh geometry
was available through flattened `xyz` coordinates.

## Existing Parser Compatibility

`loreflection/builders/scene_package_builder.py` already supports most required
raw patterns:

- `scene.room` / `scene.rooms`;
- `room.children`;
- `child.ref -> furniture.uid`;
- `pos`, `position`, `translate`;
- quaternion `rot` / `rotation`;
- `scale`;
- furniture `size` and `bbox`;
- floor-mesh and room-bbox boundary fallbacks;
- category mapping through 3D-FUTURE metadata.

It cannot be used unchanged for the current P0 output because its historical
entry point assumes one configured 3D-FUTURE root and older renderer/palette
interfaces. The new raw adapter reuses its vector and rotation helpers while
writing the current frozen-registry Architecture JSON and layout JSON.

## Recommendation

Recommended source mode:

```text
source_mode=raw_3dfront
```

Reason:

- the raw scene files and model metadata are present and readable;
- room-level furniture and floor-mesh links are explicit;
- direct room conversion preserves source provenance;
- a separate intermediate real scene package is not required for P0.

`real_scene_package` remains supported as a fallback when a previously converted
package provides both `architecture_json` and `layout_json`.

## Probe Conclusions

1. `DATA_ROOT` exists: **yes**.
2. Scene JSON location: `DATA_ROOT/3D-FRONT/*.json`.
3. `model_info.json`: found in all four `3D-FUTURE-model-part*` directories.
4. Texture and model directories: present.
5. Scene top-level fields: verified above.
6. Room, furniture, mesh, children, position, rotation, and scale: present.
7. Existing parser compatibility: mostly compatible and reused through helpers.
8. Selected conversion route: direct `raw_3dfront` room adapter.

No model training was run during this probe.
