# SemLayoutDiff Visualization Reference

This note records read-only evidence from the local SemLayoutDiff repository. It is a visualization reference, not a converter implementation transplant.

## Evidence Types
- Hard source evidence: files and keyword hits found in SemLayoutDiff source or metadata.
- Existing processed-output evidence: already existing label/color/annotation files found on disk.
- Inference: LoReflection interpretation for audit-view design.

## Main Findings
- Raw top-down render entry: `preprocess/semlayout/render_dataset_improved_mat.py and preprocess/semlayout/multi_render.py if present`.
- Semantic / architecture extraction entry: `preprocess/scripts/data_processor.py, preprocess/scripts/data_to_npy.py, and front3d visualization helpers if present`.
- Orthographic camera policy: `hard_source_evidence_found`.
- Room framing / padding policy: `hard_source_evidence_found`.
- Category-to-color policy: `metadata color palette / semantic_color_index files`.
- Built-in human-facing legend support: `False`.
- Legend note: SemLayoutDiff provides palette/color mappings, but no verified built-in human-facing legend generator was found. LoReflection legend is an audit visualization enhancement.

## LoReflection Use
- Reuse palette discipline and top-down audit framing ideas.
- Keep canonical machine-facing images separate from human-facing audit overlays.
- Add LoReflection legends only in `visual_audit_v2`; do not write legends into training label maps.

## Do Not Reuse Blindly
- Do not run Blender/BlenderProc in this audit-only step.
- Do not treat processed SemLayoutDiff PNGs as LoReflection raw source.
- Do not copy project-specific rendering code blindly into the converter.
