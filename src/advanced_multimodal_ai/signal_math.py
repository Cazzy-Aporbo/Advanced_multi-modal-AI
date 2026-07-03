from __future__ import annotations

import math
from typing import Dict

import numpy as np

from .contracts import InferenceRequest, OutputSummary


def arrays_from_request(request: InferenceRequest) -> Dict[str, np.ndarray]:
    arrays: Dict[str, np.ndarray] = {}
    batch_size = None
    for modality, payload in request.modalities.items():
        array = np.asarray(payload.values, dtype=np.float32).reshape(payload.shape)
        if batch_size is None:
            batch_size = array.shape[0]
        elif array.shape[0] != batch_size:
            raise ValueError("All modalities must share the same batch dimension")
        arrays[modality] = array
    return arrays


def output_summary(array: np.ndarray) -> OutputSummary:
    return OutputSummary(
        shape=list(array.shape),
        mean=float(array.mean()),
        std=float(array.std()),
        min=float(array.min()),
        max=float(array.max()),
    )


def signature(array: np.ndarray) -> np.ndarray:
    batch = array.shape[0]
    flattened = array.reshape(batch, -1)
    deltas = (
        np.diff(flattened, axis=1)
        if flattened.shape[1] > 1
        else np.zeros((batch, 1), dtype=np.float32)
    )
    return np.stack(
        [
            flattened.mean(axis=1),
            flattened.std(axis=1),
            flattened.min(axis=1),
            flattened.max(axis=1),
            np.abs(flattened).mean(axis=1),
            np.sqrt((flattened**2).mean(axis=1)),
            np.abs(deltas).mean(axis=1),
            (np.abs(flattened) < 1e-6).mean(axis=1),
        ],
        axis=1,
    ).astype(np.float32)


def cosine_alignment(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def normalized_entropy(values: np.ndarray, bins: int = 12) -> float:
    finite_values = values[np.isfinite(values)]
    if finite_values.size <= 1:
        return 0.0
    lower = float(finite_values.min())
    upper = float(finite_values.max())
    if math.isclose(lower, upper):
        return 0.0
    histogram_bins = min(bins, max(2, finite_values.size))
    counts, _ = np.histogram(finite_values, bins=histogram_bins, range=(lower, upper))
    total = counts.sum()
    if total == 0:
        return 0.0
    probabilities = counts[counts > 0] / total
    entropy = float(-(probabilities * np.log2(probabilities)).sum())
    max_entropy = math.log2(histogram_bins)
    return entropy / max_entropy if max_entropy else 0.0
