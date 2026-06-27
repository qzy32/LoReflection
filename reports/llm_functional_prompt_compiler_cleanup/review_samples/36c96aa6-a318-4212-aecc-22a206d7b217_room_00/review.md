# LLM Functional Prompt Compiler Review

sample_id: `36c96aa6-a318-4212-aecc-22a206d7b217_room_00`
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
Context_Control. Create a top-down fixed-palette semantic livingroom layout. Include the required semantic furniture categories: coffee_table, dining_chair, dining_table. Keep furniture inside the room floor region, preserve openings, and avoid blocking usable access. Use the architecture condition image for the room floor boundary and visible doors. Arrange the room for clear indoor function using only allowed semantic categories. Use only the frozen semantic palette. Active semantic category RGB palette entries: coffee_table=(78,224,72), dining_chair=(224,72,174), dining_table=(224,103,72).
```
