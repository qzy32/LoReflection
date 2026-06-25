# SemLayoutDiff Source Reuse Map

LoReflection uses SemLayoutDiff and its local `threed_front` parser as source
evidence for reliable preprocessing policy. R7 does not copy third-party
function bodies into LoReflection; it keeps the implementation native and
records source-level references.

| Source | Reuse mode | LoReflection use |
| --- | --- | --- |
| `preprocess/scripts/pickle_threed_front_dataset.py` | reference only | Parser entry evidence for raw 3D-FRONT / 3D-FUTURE inputs. |
| `preprocess/threed_front/datasets/parse_utils.py` | reimplement with attribution | Parser policy for linking scene children, furniture metadata, and model info. |
| `preprocess/scripts/data_processor.py` | reference only | Semantic/instance output policy evidence. |
| `preprocess/metadata/*.json`, `*.csv` | reference only | Category/index/color policy evidence, adapted to LoReflection palette. |

## Non-Reused Components

The diffusion model, trainer, checkpoint loader, sampling pipeline, and model
evaluation scripts remain outside LoReflection's native preprocessing code.
SemLayoutDiff can still be run independently as a baseline.

## Attribution

Any future copy-and-modify reuse must update
`third_party_notices/SEMLAYOUTDIFF_AND_THREED_FRONT.md` with the original file,
license, copied functions, modification notes, and date.
