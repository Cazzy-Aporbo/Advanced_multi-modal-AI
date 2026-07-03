from __future__ import annotations

from itertools import combinations
from typing import List

import numpy as np

from .contracts import (
    DataProfileResponse,
    InferenceRequest,
    ModalityQualityProfile,
    PairwiseAlignmentProfile,
)
from .signal_math import arrays_from_request, cosine_alignment, normalized_entropy, signature


def _modality_profile(modality: str, array: np.ndarray) -> ModalityQualityProfile:
    flattened = array.reshape(array.shape[0], -1)
    finite_mask = np.isfinite(flattened)
    finite_ratio = float(finite_mask.mean())
    safe = np.where(finite_mask, flattened, 0.0)
    zero_ratio = float((np.abs(safe) < 1e-6).mean())
    dynamic_range = float(np.max(safe) - np.min(safe))
    diffs = np.diff(flattened, axis=1) if flattened.shape[1] > 1 else np.zeros_like(flattened)
    temporal_change = float(np.abs(diffs).mean()) if diffs.size else 0.0
    entropy_score = normalized_entropy(flattened.reshape(-1))
    energy_score = float(np.sqrt((safe**2).mean()))

    notes: List[str] = []
    status = "ok"
    if finite_ratio < 1.0:
        notes.append("Non-finite values were detected and should be repaired before indexing.")
        status = "fail"
    if zero_ratio > 0.97:
        notes.append("The lane is almost entirely empty or zero-valued.")
        status = "fail"
    elif zero_ratio > 0.8:
        notes.append("The lane is sparse enough that retrieval and fusion may become brittle.")
        status = "watch" if status == "ok" else status
    if entropy_score < 0.08:
        notes.append("Variation is low; this modality may be repeating one pattern.")
        status = "watch" if status == "ok" else status
    if dynamic_range < 1e-5:
        notes.append("Dynamic range is effectively flat.")
        status = "watch" if status == "ok" else status
    if temporal_change == 0.0 and flattened.shape[1] > 1:
        notes.append("Adjacent values do not change across the current window.")
        status = "watch" if status == "ok" else status

    return ModalityQualityProfile(
        modality=modality,
        batch_size=int(array.shape[0]),
        feature_width=int(flattened.shape[1]),
        value_count=int(flattened.size),
        finite_ratio=finite_ratio,
        zero_ratio=zero_ratio,
        entropy_score=entropy_score,
        energy_score=energy_score,
        dynamic_range=dynamic_range,
        temporal_change=temporal_change,
        status=status,
        notes=notes,
    )


def build_data_profile(request: InferenceRequest) -> DataProfileResponse:
    arrays = arrays_from_request(request)
    modality_profiles = [
        _modality_profile(modality, array) for modality, array in sorted(arrays.items())
    ]

    signatures = {modality: signature(array).mean(axis=0) for modality, array in arrays.items()}
    pairwise_alignment: List[PairwiseAlignmentProfile] = []
    pairwise_scores: List[float] = []

    for left, right in combinations(sorted(signatures.keys()), 2):
        left_vector = signatures[left]
        right_vector = signatures[right]
        alignment = cosine_alignment(left_vector, right_vector)
        pairwise_scores.append((alignment + 1.0) / 2.0)
        mean_gap = float(np.abs(left_vector - right_vector).mean())
        note = (
            "The two lanes compress into similar signature geometry."
            if alignment >= 0.7
            else "The two lanes are pulling apart and should be reviewed before shared fusion."
        )
        pairwise_alignment.append(
            PairwiseAlignmentProfile(
                left_modality=left,
                right_modality=right,
                cosine_alignment=alignment,
                mean_gap=mean_gap,
                note=note,
            )
        )

    coverage_score = float(
        np.mean(
            [
                (profile.finite_ratio + (1.0 - profile.zero_ratio)) / 2.0
                for profile in modality_profiles
            ]
        )
    )
    pairwise_mean = float(np.mean(pairwise_scores)) if pairwise_scores else 1.0
    fusion_readiness = max(0.0, min(1.0, (coverage_score * 0.6) + (pairwise_mean * 0.4)))

    warnings: List[str] = []
    failing_modalities = [
        profile.modality for profile in modality_profiles if profile.status == "fail"
    ]
    watching_modalities = [
        profile.modality for profile in modality_profiles if profile.status == "watch"
    ]
    if failing_modalities:
        warnings.append(
            "Immediate cleanup is required for: " + ", ".join(sorted(failing_modalities)) + "."
        )
    if watching_modalities:
        warnings.append(
            "Proceed carefully with: " + ", ".join(sorted(watching_modalities)) + "."
        )
    if pairwise_alignment and pairwise_mean < 0.45:
        warnings.append(
            "Cross-modal signatures are weakly aligned, so any fused story should "
            "remain provisional."
        )

    return DataProfileResponse(
        request_id=str(request.metadata.get("request_id", request.model_id)),
        model_id=request.model_id,
        runtime_mode=request.runtime_mode,
        modality_profiles=modality_profiles,
        pairwise_alignment=pairwise_alignment,
        coverage_score=coverage_score,
        fusion_readiness=fusion_readiness,
        warnings=warnings,
    )
