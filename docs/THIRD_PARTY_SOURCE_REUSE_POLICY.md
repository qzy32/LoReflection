# Third-Party Source Reuse Policy

## Policy

LoReflection may use SemLayoutDiff and its local `threed_front` parser stack as
source-level evidence for preprocessing behavior, but third-party code must not
be copied into LoReflection without license review and attribution.

Allowed reuse modes:

- `reference_only`: cite source behavior and implement native LoReflection code.
- `reimplement_with_attribution`: reimplement the behavior and record the source
  files that informed the implementation.
- `wrap_directly`: call an installed dependency through a narrow wrapper when
  the dependency version and license are known.
- `copy_and_modify`: allowed only after confirming the license permits it and
  adding source headers and notices.

## R7 Decision

R7 performs no copy-and-modify reuse of third-party function bodies. It refactors
LoReflection's own raw-data converter into a native package and records
SemLayoutDiff / `threed_front` sources as evidence and future reuse candidates.

## Required Notice Fields

Any future copied or modified third-party function must record:

- original repository;
- original file path;
- license;
- original copyright notice;
- copied or modified function names;
- LoReflection destination file;
- modifications;
- modification date.

## Stop Conditions

Stop implementation and ask for review if:

- the upstream license is missing or incompatible;
- the needed parser source is unavailable;
- behavior cannot be verified without downloading dependencies or running
  Blender/BlenderProc;
- the reuse would require changing LoReflection schema or category taxonomy.
