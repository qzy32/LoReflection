# Data Provenance Policy

## Current Source Wording

Use this wording for the current server bundle:

```text
EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle
```

Do not describe it as a freshly downloaded official 3D-FRONT / 3D-FUTURE archive.

## Allowed Prototype Uses

- Converter prototype.
- Field mapping.
- Val50 prototype.
- Debugging LoReflection schema and data flow.

## Not Recommended Without Additional Verification

- Final main experiment without provenance disclosure.
- Claiming official raw dataset provenance.
- Strict baseline comparison without split alignment.

## Required Before Main Experiments

- Obtain official raw bundles or verify checksums / splits against the official source.
- Document provenance in the paper and experiment logs.
- Run converter regression on the official or verified source.
- Freeze train / val / test split.

## Migration Policy

If an official raw bundle is obtained:

1. Place official bundle under `/wuqingyaoa800/qiuziyan/datasets/official_3dfront_bundle`.
2. Rerun provenance check.
3. Rerun field mapping report.
4. Rerun 5-scene converter prototype.
5. Compare category histogram, jid match, and room type distribution.
6. Rerun val50.
7. Only then build training 1k.
