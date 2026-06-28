# LLM Functional Prompt Compiler Review

sample_id: `faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05`
room_type: `livingroom`

## Checks

- LLM input contains coordinates: no
- LLM output contains coordinates: no
- PromptPackage schema status: `pass`
- Geometry leakage: `[]`
- Architecture claim issues: `[]`
- Rule fallback used: no

## Prompt

```text
Context_Control. Create a top-down fixed-palette semantic livingroom layout. Include the required semantic furniture categories: ceiling_lamp, coffee_table, desk, lazy_sofa, multi_seat_sofa, table, tv_stand. Keep furniture inside the room floor region, preserve openings, and avoid blocking usable access. Use the architecture condition image for the room floor boundary and visible doors and visible windows. Arrange the room for clear indoor function using only allowed semantic categories. Use only the frozen semantic palette. Active semantic category RGB palette entries: ceiling_lamp=(72,104,224), coffee_table=(78,224,72), desk=(212,224,72), lazy_sofa=(72,136,224), multi_seat_sofa=(224,72,224), table=(72,224,148), tv_stand=(72,167,224).
```
