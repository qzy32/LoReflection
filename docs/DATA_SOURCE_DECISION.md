# Data Source Decision

## Current Decision

Current EditRoom-provided bundle is allowed for converter prototype and val50-prototype debugging, but should not be described as a freshly downloaded official 3D-FRONT / 3D-FUTURE archive.

The current server bundle is located under:

```text
/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/3D-FRONT
```

It has an official-like 3D-FRONT / 3D-FUTURE structure, including scene JSON, texture directory, `model_info.json`, and model directories. However, because it is distributed inside an EditRoom dataset tree and includes preprocessed files such as `threed_front.pkl`, LoReflection should record it as an EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle.

## Final Experiment Policy

For main experiments, prefer official raw 3D-FRONT / 3D-FUTURE / texture bundles or explicitly disclose the use of the EditRoom-provided preprocessed bundle.

Before final main experiments, run provenance and split checks, freeze train/val/test splits, and rerun converter regression on the official or verified source.

## Reporting Wording

Prototype stage:

```text
EditRoom-provided 3D-FRONT / 3D-FUTURE-based bundle
```

Final paper if official raw source is obtained:

```text
3D-FRONT and 3D-FUTURE official datasets
```

Final paper if only EditRoom bundle is used:

```text
the 3D-FRONT / 3D-FUTURE-based preprocessed bundle released with EditRoom
```

## Allowed Uses

- Converter prototype.
- Field mapping.
- Val50 prototype.
- Debugging LoReflection data and schema flow.

## Not Recommended Without Additional Verification

- Claiming use of freshly downloaded official raw archives.
- Final main experiment without provenance disclosure.
- Strict baseline comparison without split alignment.

## Migration Plan

If an official raw bundle is obtained:

1. Place official bundle under `/wuqingyaoa800/qiuziyan/datasets/official_3dfront_bundle`.
2. Rerun provenance check.
3. Rerun field mapping report.
4. Rerun 5-scene converter prototype.
5. Compare category histogram / jid match / room type distribution.
6. Rerun val50.
7. Only then build training 1k.
