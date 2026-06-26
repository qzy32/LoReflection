# Rule Template Prompt Correctness Audit

Status: **NOT VERIFIED locally** because the server P1 metadata directories are not present in this local snapshot.

The new audit checks:

- required category coverage;
- required count wording;
- room type mismatch risk;
- extra furniture categories not present in Goal LoState;
- appearance/style/material/color words;
- architecture condition image mention;
- frozen semantic palette / `Palette_Control`;
- geometry leakage.

Dangerous wording explicitly flagged includes `specific color palette designated for elderlyroom`, `correct color palette`, `beautiful`, `modern`, `cozy`, `wood`, `fabric`, `material`, and `texture`.
