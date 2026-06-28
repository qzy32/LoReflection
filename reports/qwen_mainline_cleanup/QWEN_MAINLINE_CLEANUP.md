# Qwen Mainline Cleanup

## Scope

This cleanup removes tracked Qwen artifacts that are not part of the current
`full_semantic_compiled_main` route.

Current retained mainline:

- LLM Functional Prompt Compiler only.
- Qwen Architecture In-Context metadata with exactly:
  `image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs`.
- `image = target_full_semantic`.
- `context_image = architecture_condition_image`.
- StatePatch editor handoff and executor-facing schemas.

## Removed

- Retired Qwen repair training configs and scripts.
- Retired prompt ablation / prompt-label variant tools and tests.
- Retired auxiliary target reports and review packages.
- Retired server dry-run path templates and historical report files.
- Retired RepairPlan/mask-spec current-interface schemas and tests.
- Retired tracked archive files for the previous route.

## Validation

- Deprecated Qwen route term scan: pass.
- `git diff --check`: pass.
- Pytest targeted current Qwen/StatePatch suite: `72 passed`.

## Runtime Safety

No data package, model checkpoint, training output, or running process was
modified by this cleanup.
