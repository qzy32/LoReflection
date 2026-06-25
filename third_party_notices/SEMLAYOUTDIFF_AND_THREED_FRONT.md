# SemLayoutDiff And threed_front Source Notice

## Original Sources

- SemLayoutDiff: `https://github.com/3dlg-hcvc/SemLayoutDiff`
- Local SemLayoutDiff checkout used for evidence:
  `/wuqingyaoa800/qiuziyan/DiffSynth-Studio-apm-stage1-rotY/SemLayoutDiff_update_20260312_163509`
- Local parser evidence:
  `preprocess/threed_front/datasets/parse_utils.py`

## R7 Reuse Status

No SemLayoutDiff or `threed_front` function body is copied into LoReflection in
R7. LoReflection uses these sources as reference evidence and keeps the native
preprocessing implementation in the `loreflection` package.

## Files Considered

| Original file | LoReflection use | Reuse mode |
| --- | --- | --- |
| `preprocess/scripts/pickle_threed_front_dataset.py` | parser entry evidence | reference only |
| `preprocess/threed_front/datasets/parse_utils.py` | parser/link policy evidence | reimplement with attribution |
| `preprocess/scripts/data_processor.py` | semantic/instance policy evidence | reference only |
| `preprocess/metadata/*` | category/index/color evidence | reference only |

## Future Copy-And-Modify Checklist

Before copying any code, add:

- original copyright header;
- license text/reference;
- original repository and file path;
- copied function names;
- LoReflection destination path;
- modification summary and date.
