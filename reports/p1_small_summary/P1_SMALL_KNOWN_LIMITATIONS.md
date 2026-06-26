# P1-small Known Limitations

P1-small is a normalized_v1 baseline for Architecture In-Context route validation. It is not the final P1/P2 data contract.

## Scale

The current normalized_v1 renderer scales each room to a fixed image size. This keeps image training simple and makes the route test cheap, but the condition image does not explicitly preserve absolute room-size differences. Before P1-1000, add explicit `metric_transform` metadata or move to metric_v2 rendering.

## Room Type

Room type recovery is still not treated as a blocking contract. Some reports may show unknown room types depending on whether they read metadata, layout JSON, or sample manifests. Before P1-1000, standardize room type extraction from raw 3D-FRONT room fields and furniture composition.

## Evaluation

P1-small evaluates 20 inference samples from a 200-sample training run. It is a baseline sanity result, not a final model-quality conclusion.
