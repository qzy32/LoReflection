# LoReflection vs Reference Comparison

| item | LoReflection current | reference project | should LoReflection change? |
|---|---|---|---|
| target image | Furniture colors over void/background; no structural floor/door/window/wall pixels in the audited sample. | Full semantic map: architecture/no-furniture base plus furniture overlay. | Yes, add a full-semantic target ablation. |
| context image | Architecture-only condition from raw 3D-FRONT-derived Architecture JSON. | No-furniture architecture/room condition. | Keep. |
| prompt | Context_Control prompt plus optional LLM/template variants and palette contract packages. | Room semantic prompt with constraints and palette legend. | Keep LoReflection prompt system; optionally add palette-control compiled prompts. |
| metadata fields | `image,prompt,context_image,sample_id,goal_lostate,prompt_package,verifier_refs`. `image` currently points to furniture-only target. | `image,context_image/kontext_images,prompt,...`; `image` points to with-furniture full semantic target. | For full target route, set `image=target_full_semantic` and preserve `target_furniture_only` as extra field. |
| palette | LoReflection frozen semantic registry v2. | Reference 34-class c2rgb/id2c. | Do not copy values; reuse validation pattern only. |
| architecture preservation | Preserved outside Qwen output by parser/furniture-only interpretation. | Target itself includes architecture and protected-pixel checks. | Add protected architecture overwrite audit. |
| output interpretation | Qwen output is interpreted as furniture layer. | Qwen output is full semantic map. | If user wants complete layout image, add full-map route. |
| evaluation | Furniture pixel agreement/F1 plus palette checks. | Needs full semantic and protected architecture checks. | Extend eval before judging full-map training. |

## Decision

LoReflection should not delete the furniture-only route because it is useful for parsing furniture masks back to metric layout. But for the user-facing and paper-facing claim that Qwen generates a complete semantic layout on top of architecture, LoReflection should add a full-semantic target route and run a controlled ablation before P1-1000.
