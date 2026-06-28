# LLM Functional Prompt Compiler Review

sample_id: `faf62fbc-739a-40da-aac3-12b6807ee7e3_room_02`
room_type: `courtyard`

## Checks

- LLM input contains coordinates: no
- LLM output contains coordinates: no
- PromptPackage schema status: `pass`
- Geometry leakage: `[]`
- Architecture claim issues: `[]`
- Rule fallback used: no

## Prompt

```text
Context_Control. Create a top-down fixed-palette semantic courtyard layout. Include the required semantic furniture categories: corner_side_table, desk, lounge_chair, pendant_lamp. Keep furniture inside the room floor region, preserve openings, and avoid blocking usable access. Use the architecture condition image for the room floor boundary and visible doors and visible windows. Arrange the room for clear indoor function using only allowed semantic categories. Use only the frozen semantic palette. Active semantic category RGB palette entries: corner_side_table=(224,154,72), desk=(212,224,72), lounge_chair=(72,224,97), pendant_lamp=(224,84,72).
```
