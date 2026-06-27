# Training Readiness After LLM Apply

status: BLOCKED
blocked_gate: strict LLM prompt shard apply

## Summary

- Dataset root: `/wuqingyaoa800/qiuziyan/LoReflection_arch_p0/data/loreflection_qwen_arch_control_full_metric_v2_full_semantic_compiled`
- Metadata rows: `4879`
- Apply status: `fail`
- Applied to metadata: no
- Updated metadata prompt rows: `0`
- Updated prompt package files: `0`
- Fallback false rows: `4870 / 4879`
- Fallback true rows: `9`
- Ready for training: `False`
- Training started: no

## Blocker

Strict apply refused to modify the formal dataset because 9 shard rows have `fallback_used=true` / validation failed. This is a shard quality gate failure, not an LLM client availability failure.

## Fallback Rows

- `14ef0cd9-ba3e-4b97-afee-d4f53a0eb7d7_room_02`
- `6e18eae0-40b9-43e8-a718-11ebf2f73051_room_04`
- `a065a8b5-2593-489b-949f-9334f982dddb_room_19`
- `f50e31b6-7aba-4d78-8847-1822f568fa3e_room_00`
- `51508cc8-618a-4537-b753-53a381c1af0d_room_01`
- `36a434a5-ed7a-4f92-ba94-57685e289b37_room_00`
- `e3681044-5e15-41f4-9d87-49746b7f26ec_room_03`
- `d2e1869f-9e98-4169-8643-28cb1be0ef41_room_01`
- `b8d5c14b-b931-4b1e-969f-b96f5c1f3bb5_room_00`

## Required Next Step

Regenerate or repair only these 9 prompt shard rows with the current LLM-only compiler, then rerun strict apply. Do not train until `fallback_false_rows == metadata_rows` and `applied == true`.
