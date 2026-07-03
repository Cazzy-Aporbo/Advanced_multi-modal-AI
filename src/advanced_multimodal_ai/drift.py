from __future__ import annotations

from statistics import mean
from typing import Dict, Iterable, List

from .contracts import (
    DataProfileResponse,
    DriftBaselineRecord,
    DriftBaselineRequest,
    ModalityDriftDelta,
    ModalityQualityProfile,
    PairwiseAlignmentProfile,
    PopulationDriftRequest,
    PopulationDriftResponse,
)


def create_drift_baseline_record(
    request: DriftBaselineRequest,
    profile: DataProfileResponse,
) -> DriftBaselineRecord:
    return DriftBaselineRecord(
        label=request.label,
        request_id=profile.request_id,
        model_id=profile.model_id,
        runtime_mode=profile.runtime_mode,
        coverage_score=profile.coverage_score,
        fusion_readiness=profile.fusion_readiness,
        modality_profiles=profile.modality_profiles,
        pairwise_alignment=profile.pairwise_alignment,
        notes=request.notes,
    )


def assess_population_drift(
    baseline: DriftBaselineRecord,
    current_profile: DataProfileResponse,
    request: PopulationDriftRequest,
) -> PopulationDriftResponse:
    baseline_profiles = {profile.modality: profile for profile in baseline.modality_profiles}
    current_profiles = {profile.modality: profile for profile in current_profile.modality_profiles}

    deltas: List[ModalityDriftDelta] = []
    scores: List[float] = []
    warnings: List[str] = []
    recommendations: List[str] = []

    for modality in sorted(set(baseline_profiles) | set(current_profiles)):
        baseline_profile = baseline_profiles.get(modality)
        current_modality_profile = current_profiles.get(modality)
        delta = _build_modality_delta(
            modality=modality,
            baseline_profile=baseline_profile,
            current_profile=current_modality_profile,
            request=request,
        )
        deltas.append(delta)
        scores.append(
            _modality_risk_score(
                delta=delta,
                current_profile=current_modality_profile,
                request=request,
            )
        )
        if delta.status == "fail":
            warnings.append(
                f"{modality} moved outside the prepared population window and should be reviewed."
            )
        elif delta.status == "watch":
            warnings.append(f"{modality} is shifting and may need recalibration.")

    baseline_alignment = _alignment_mean(baseline.pairwise_alignment)
    current_alignment = _alignment_mean(current_profile.pairwise_alignment)
    alignment_drop = max(0.0, baseline_alignment - current_alignment)
    alignment_score = min(1.0, alignment_drop / max(request.max_alignment_drop, 1e-6))
    scores.append(alignment_score)

    if alignment_drop > request.max_alignment_drop:
        warnings.append(
            "Cross-modal agreement has fallen below the prepared alignment boundary."
        )
        recommendations.append(
            "Review ingestion timing, modality synchronization, "
            "and source consistency before reuse."
        )

    baseline_modalities = set(baseline_profiles)
    current_modalities = set(current_profiles)
    missing_modalities = sorted(baseline_modalities - current_modalities)
    new_modalities = sorted(current_modalities - baseline_modalities)
    if missing_modalities:
        warnings.append(
            "The current request is missing expected lanes: " + ", ".join(missing_modalities) + "."
        )
        recommendations.append(
            "Restore the missing modality lanes or prepare a narrower baseline for this route."
        )
    if new_modalities:
        warnings.append(
            "New modality lanes appeared outside the saved baseline: "
            + ", ".join(new_modalities)
            + "."
        )
        recommendations.append(
            "Review whether the new lanes belong to the same population before fusing them."
        )

    drift_score = float(mean(scores)) if scores else 0.0
    blocked = request.block_on_failure and (
        any(delta.status == "fail" for delta in deltas)
        or alignment_drop > request.max_alignment_drop
    )

    if blocked:
        recommendations.append(
            "Hold this population out of production inference until "
            "the boundary is reset with reviewed data."
        )
    elif drift_score > 0.45:
        recommendations.append(
            "The population is still usable, but it has moved "
            "far enough to justify a fresh baseline review."
        )

    if current_profile.coverage_score + 0.12 < baseline.coverage_score:
        warnings.append("Coverage fell materially below the saved population baseline.")
        recommendations.append(
            "Inspect sparsity, silent tensors, and missing fields "
            "before drawing conclusions from this run."
        )

    return PopulationDriftResponse(
        baseline_label=baseline.label,
        request_id=current_profile.request_id,
        model_id=current_profile.model_id,
        drift_score=max(0.0, min(1.0, drift_score)),
        blocked=blocked,
        modality_deltas=deltas,
        alignment_drop=alignment_drop,
        warnings=_dedupe_keep_order(warnings),
        recommendations=_dedupe_keep_order(recommendations),
    )


def _build_modality_delta(
    modality: str,
    baseline_profile: ModalityQualityProfile | None,
    current_profile: ModalityQualityProfile | None,
    request: PopulationDriftRequest,
) -> ModalityDriftDelta:
    if baseline_profile is None and current_profile is not None:
        return ModalityDriftDelta(
            modality=modality,
            entropy_shift=1.0,
            zero_shift=1.0,
            finite_shift=current_profile.finite_ratio,
            dynamic_range_shift=1.0,
            temporal_change_shift=1.0,
            status="watch",
            notes=["This modality is new to the current request and has no saved baseline."],
        )
    if baseline_profile is not None and current_profile is None:
        return ModalityDriftDelta(
            modality=modality,
            entropy_shift=baseline_profile.entropy_score,
            zero_shift=baseline_profile.zero_ratio,
            finite_shift=-baseline_profile.finite_ratio,
            dynamic_range_shift=1.0,
            temporal_change_shift=1.0,
            status="fail",
            notes=[
                "This modality was present in the baseline but is absent "
                "from the current request."
            ],
        )

    assert baseline_profile is not None
    assert current_profile is not None

    entropy_shift = abs(current_profile.entropy_score - baseline_profile.entropy_score)
    zero_shift = abs(current_profile.zero_ratio - baseline_profile.zero_ratio)
    finite_shift = current_profile.finite_ratio - baseline_profile.finite_ratio
    dynamic_range_shift = _relative_shift(
        baseline_profile.dynamic_range, current_profile.dynamic_range
    )
    temporal_change_shift = _relative_shift(
        baseline_profile.temporal_change, current_profile.temporal_change
    )

    notes: List[str] = []
    status = "ok"

    if current_profile.finite_ratio < request.min_finite_ratio:
        notes.append("Finite value coverage dropped below the accepted boundary.")
        status = "fail"
    if entropy_shift > request.max_entropy_shift:
        notes.append("Variation shifted too far from the prepared population.")
        status = "fail"
    elif entropy_shift > request.max_entropy_shift * 0.6:
        notes.append("Variation is moving and should be watched.")
        status = "watch" if status == "ok" else status
    if zero_shift > request.max_zero_shift:
        notes.append("Sparsity moved outside the accepted band.")
        status = "fail"
    elif zero_shift > request.max_zero_shift * 0.6:
        notes.append("Sparsity is drifting and may change retrieval behaviour.")
        status = "watch" if status == "ok" else status
    if dynamic_range_shift > 0.6:
        notes.append("Dynamic range changed sharply from the saved baseline.")
        status = "watch" if status == "ok" else status
    if temporal_change_shift > 0.6:
        notes.append("Local temporal motion changed sharply from the saved baseline.")
        status = "watch" if status == "ok" else status
    if current_profile.status == "fail":
        status = "fail"
        notes.extend(current_profile.notes)
    elif current_profile.status == "watch" and status == "ok":
        status = "watch"
        notes.extend(current_profile.notes)

    return ModalityDriftDelta(
        modality=modality,
        entropy_shift=entropy_shift,
        zero_shift=zero_shift,
        finite_shift=finite_shift,
        dynamic_range_shift=dynamic_range_shift,
        temporal_change_shift=temporal_change_shift,
        status=status,
        notes=_dedupe_keep_order(notes),
    )


def _modality_risk_score(
    delta: ModalityDriftDelta,
    current_profile: ModalityQualityProfile | None,
    request: PopulationDriftRequest,
) -> float:
    entropy_score = min(1.0, delta.entropy_shift / max(request.max_entropy_shift, 1e-6))
    zero_score = min(1.0, delta.zero_shift / max(request.max_zero_shift, 1e-6))
    range_score = min(1.0, delta.dynamic_range_shift)
    temporal_score = min(1.0, delta.temporal_change_shift)

    finite_score = 0.0
    if current_profile is not None and current_profile.finite_ratio < request.min_finite_ratio:
        finite_score = min(
            1.0,
            (request.min_finite_ratio - current_profile.finite_ratio)
            / max(request.min_finite_ratio, 1e-6),
        )

    return max(entropy_score, zero_score, range_score, temporal_score, finite_score)


def _alignment_mean(profiles: Iterable[PairwiseAlignmentProfile]) -> float:
    values = [max(0.0, min(1.0, (profile.cosine_alignment + 1.0) / 2.0)) for profile in profiles]
    return float(mean(values)) if values else 1.0


def _relative_shift(baseline_value: float, current_value: float) -> float:
    scale = max(abs(baseline_value), abs(current_value), 1e-6)
    return abs(current_value - baseline_value) / scale


def _dedupe_keep_order(values: List[str]) -> List[str]:
    seen: Dict[str, None] = {}
    return [seen.setdefault(value, None) or value for value in values if value not in seen]
