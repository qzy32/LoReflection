# Native 3D-FRONT Preprocessing Pipeline

## Scope

The native pipeline reads raw 3D-FRONT scene JSON and 3D-FUTURE
`model_info.json` directly. It does not treat SemLayoutDiff processed PNG/JSON
as source data.

## Modules

- `loreflection.data.front3d.scene_parser`: scene id, rooms, room children,
  furniture metadata, and child transform links.
- `loreflection.data.front3d.future_registry`: `model_id` / `jid` to
  3D-FUTURE metadata.
- `loreflection.data.front3d.category_mapper`: raw category to LoReflection
  canonical action, semantic group, and palette category.
- `loreflection.data.front3d.room_geometry`: floor mesh, boundary polygon,
  derived wall segments, door/window anchors, and room bounds.
- `loreflection.data.front3d.furniture_geometry`: furniture transform,
  footprint, bbox, centroid, orientation, and source provenance.
- `loreflection.data.front3d.coordinate_transform`: world-to-image transform
  shared by architecture condition, semantic layout, and audit overlays.
- `loreflection.rendering.topdown`: canonical top-down rendering helpers.
- `loreflection.builders.scene_package_builder`: scene package orchestration.

## Parsed Furniture Fields

| Field | Source | Type / unit | Required | Fallback | Consumed by |
| --- | --- | --- | --- | --- | --- |
| `uid` | top-level `furniture[].uid` | string | yes | none | transform link |
| `jid` | top-level `furniture[].jid` | string | no | empty jid warning | category lookup |
| `child_ref` | `scene.room[*].children[*].ref` | string | yes for transform | uid/jid fallback rules | geometry |
| `position` | child `pos` | meters candidate | yes for placed entity | prior/grid warning | renderer |
| `rotation` | child `rot` | quaternion candidate | no | yaw 0 warning | renderer |
| `scale` | child `scale` | scalar/vector | no | `[1,1,1]` | footprint |
| `raw_category` | 3D-FUTURE `model_info.category` | string | yes for known furniture | unknown mapping | reports |
| `reference_category` | category mapping config | string | yes for mapped categories | unknown | reports |
| `loreflection_category` | category mapping config | string | required for `keep_furniture` | strict fail | semantic output |
| `action` | category mapping config | canonical action | yes | strict fail | routing |
| `semantic_group` | category mapping config | group string | yes | strict fail | reports |
| `skip_reason` | category mapping config | string | required for `skip` | strict fail | reports |

## Geometry Fields

| Field | Source | Type / unit | Required | Fallback | Consumed by |
| --- | --- | --- | --- | --- | --- |
| `footprint_polygon_m` | transform + size / bbox candidate | world meters candidate | no | bbox rectangle | semantic rasterizer |
| `bbox_m` | footprint bounds | world meters candidate | yes for entity | category prior | Observed LoState |
| `bbox_px` | world-to-image transform | pixels | yes for rasterized entity | skip if invalid | reports |
| `centroid_m` | child position / bbox center | world meters candidate | yes | bbox center | Observed LoState |
| `orientation_deg` | child rotation yaw | degrees | no | 0 | reports/review |
| `area_m2` | footprint polygon | square meters candidate | no | bbox area | annotation |
| `transform_source` | link rule | string | yes | warning | provenance |
| `size_source` | model/metadata/category prior | string | yes | warning | provenance |
| `orientation_source` | child `rot` | string | yes | fallback | provenance |

## Architecture Fields

| Field | Source | Type / unit | Required | Fallback | Consumed by |
| --- | --- | --- | --- | --- | --- |
| `boundary.polygon_m` | floor mesh / room mesh | world coordinates | yes before scale50 | bbox fallback warning | architecture condition |
| `boundary.source` | extraction method | string | yes | `bbox_fallback` warning | validator |
| `derived_wall_segments` | boundary edges | line segments | yes if no explicit walls | none is strict fail | architecture reference |
| `door_anchors` | architecture category anchors | list | no | empty | audit/reviewer |
| `window_anchors` | architecture category anchors | list | no | empty | audit/reviewer |
| `clearance_regions` | future geometry policy | list | no | empty | architecture condition |
| `coordinate_system` | converter metadata | dict | yes | unknown unit | all renderers |
| `coordinate_transforms` | room bounds/image size | dict | yes | none | renderers |
| `against_wall_reference_source` | explicit or derived wall source | string | yes | strict fail if missing | validator |

## Observed LoState Fields

Observed LoState contains furniture instances only. It must not contain door,
window, wall, or floor entities.

| Field | Source | Consumed by |
| --- | --- | --- |
| `instance_id` | converter generated | LoRAM / reviewer |
| `category` | LoReflection palette category | semantic review |
| `mask` / `bbox` | rasterizer / geometry | State Observer |
| `centroid` | geometry | spatial checks |
| `orientation` | child rotation | alignment checks |
| `mapping_action` | category mapper | taxonomy audit |
| `semantic_group` | category mapper | reports |
| `source_jid` | 3D-FRONT/3D-FUTURE link | provenance |
| `parser_source` | native parser metadata | provenance |
| `transform_source` | child link rule | provenance |
| `size_source` | model or prior | provenance |
