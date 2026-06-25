"""Current semantic_repair4 output sanitizer utilities.

The sanitizer is intentionally post-processing/evaluation logic only. It does
not alter taxonomy, palette, model loss, or the repair action protocol.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

import numpy as np


SEMANTIC_REPAIR4 = {"ADD", "REMOVE", "TRANSLATE", "REPLACE"}
PARAMETRIC_UPDATE = {"ROTATE", "SCALE"}


@dataclass(frozen=True)
class Component:
    label: int
    area_px: int
    bbox: tuple[int, int, int, int]


def copyback_output(bad_rgb: np.ndarray, output_rgb: np.ndarray, mask_l: np.ndarray) -> np.ndarray:
    """Copy model output inside white mask and preserve bad input outside."""

    mask = mask_l > 0
    result = bad_rgb.copy()
    result[mask] = output_rgb[mask]
    return result


def exact_palette_label_map(rgb: np.ndarray, rgb_to_label: dict[tuple[int, int, int], int]) -> np.ndarray:
    """Map an exact-palette RGB image to semantic IDs, using -1 for unknown colors."""

    labels = np.full(rgb.shape[:2], -1, dtype=np.int32)
    flat = rgb.reshape(-1, 3)
    out = labels.reshape(-1)
    for color, label in rgb_to_label.items():
        matches = np.all(flat == np.asarray(color, dtype=np.uint8), axis=1)
        out[matches] = int(label)
    return labels


def palette_valid_ratio(rgb: np.ndarray, rgb_to_label: dict[tuple[int, int, int], int]) -> float:
    labels = exact_palette_label_map(rgb, rgb_to_label)
    return float((labels >= 0).mean())


def connected_components(label_map: np.ndarray, label: int) -> list[Component]:
    """4-connected components for one semantic label."""

    mask = label_map == label
    visited = np.zeros(mask.shape, dtype=bool)
    comps: list[Component] = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            visited[y, x] = True
            xs: list[int] = []
            ys: list[int] = []
            while q:
                cx, cy = q.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        q.append((nx, ny))
            comps.append(Component(label=label, area_px=len(xs), bbox=(min(xs), min(ys), max(xs) + 1, max(ys) + 1)))
    return comps


def remove_tiny_components(
    label_map: np.ndarray,
    *,
    min_component_area_px: int,
    preserve_labels: Iterable[int],
    fallback_label: int,
) -> np.ndarray:
    """Remove tiny isolated components except protected labels.

    Removed pixels are reassigned to ``fallback_label``. This is intended for
    offline diagnosis and post-copyback cleanup; it is never a training loss.
    """

    result = label_map.copy()
    preserve = set(int(x) for x in preserve_labels)
    for label in sorted(set(int(x) for x in np.unique(label_map)) - {-1}):
        if label in preserve:
            continue
        for comp in connected_components(label_map, label):
            if comp.area_px < min_component_area_px:
                x0, y0, x1, y1 = comp.bbox
                sub = label_map[y0:y1, x0:x1] == label
                result[y0:y1, x0:x1][sub] = fallback_label
    return result


def allowed_label_violations(label_map: np.ndarray, mask_l: np.ndarray, allowed_labels: set[int]) -> int:
    mask = mask_l > 0
    labels = set(int(x) for x in np.unique(label_map[mask]) if int(x) >= 0)
    return len(labels - set(int(x) for x in allowed_labels))


def pixel_accuracy(a: np.ndarray, b: np.ndarray, mask: np.ndarray | None = None) -> float:
    if mask is None:
        return float(np.all(a == b, axis=-1).mean()) if a.ndim == 3 else float((a == b).mean())
    region = mask > 0
    if not np.any(region):
        return 1.0
    if a.ndim == 3:
        return float(np.all(a[region] == b[region], axis=-1).mean())
    return float((a[region] == b[region]).mean())


def iou_binary(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / union) if union else 1.0
