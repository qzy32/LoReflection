# Qwen Generation vs Inpaint Route Decision

## Ordinary Qwen-Image LoRA

Applies to: prompt / architecture textual condition -> fixed-palette semantic layout I0.

Paper path: Goal LoState -> Prompt / Condition Builder -> Qwen-Image initial generation -> I0.

Pros: natural generation task; no need to disguise generation as inpainting; main Ours-Initial candidate.

Risks: without strong architecture image condition it may fail to preserve door/window/boundary; current ordinary overfit32 was text-only.

## DiffSynth Qwen-Image-Blockwise-ControlNet-Inpaint LoRA

Repair route: I_bad + local control_mask + correction_prompt -> repaired layout. This is Ours-Final repair executor.

Full-mask generation candidate: architecture-only canvas + floor-generation mask + generation prompt -> full semantic layout. This must be experimentally compared before replacing ordinary generation.

Mask convention from source: white/high mask is the repaint/masked region; black/low mask preserves the control image region.
