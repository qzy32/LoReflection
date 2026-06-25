# Palette Round-Trip Multiclass Audit

Observer entry: `runtime.observer.observe`. Synthetic images use active `semantic_registry_v2/palette_frozen.json`.

| scene | category acc | pixel acc | instance acc | false merge | false split | arch leakage |
|---|---:|---:|---:|---:|---:|---:|
| testA_all_object_classes | 1.000 | 1.000 | 1.000 | 0 | 0 | 0 |
| testB_mixed_room_realistic | 1.000 | 1.000 | 1.000 | 0 | 0 | 0 |
| testC_near_neighbor_stress | 1.000 | 1.000 | 1.000 | 0 | 0 | 0 |
| testD_repeated_instances | 1.000 | 1.000 | 1.000 | 0 | 0 | 0 |

Conclusion: exact-color multiclass decode is stable. Remaining risk is instance separation when same-category regions touch; these fixtures keep repeated instances separated.
