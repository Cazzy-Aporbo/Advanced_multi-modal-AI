from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

from .config import Settings
from .contracts import (
    InferenceRequest,
    ModalityKind,
    TensorInterceptProfile,
    TensorInterceptResponse,
)
from .rust_bridge import tensor_guard_from_payload
from .signal_math import arrays_from_request, normalized_entropy


def _restricted_modalities(raw_value: Any) -> List[ModalityKind]:
    if isinstance(raw_value, str):
        values = [part.strip() for part in raw_value.split(",") if part.strip()]
    elif isinstance(raw_value, Iterable):
        values = [str(item).strip() for item in raw_value if str(item).strip()]
    else:
        values = []
    allowed = {"text", "image", "audio", "video", "sensor", "tabular"}
    return [value for value in values if value in allowed]  # type: ignore[return-value]


def _normalized_spatial_frequency(flattened: np.ndarray) -> float:
    if flattened.shape[1] <= 1:
        return 0.0
    safe = np.where(np.isfinite(flattened), flattened, 0.0)
    diffs = np.diff(safe, axis=1)
    energy = float(np.sqrt((diffs**2).mean()))
    dynamic_range = float(np.max(safe) - np.min(safe))
    if math.isclose(dynamic_range, 0.0, abs_tol=1e-8):
        return 0.0
    normalized = energy / max(dynamic_range, 1e-8)
    return max(0.0, min(1.0, normalized))


def _saturation_ratio(flattened: np.ndarray) -> float:
    safe = np.where(np.isfinite(flattened), flattened, 0.0)
    max_abs = float(np.abs(safe).max())
    if max_abs <= 1e-8:
        return 0.0
    threshold = max_abs * 0.92
    return float((np.abs(safe) >= threshold).mean())


def _risk_score(
    entropy_score: float,
    spatial_frequency: float,
    saturation_ratio: float,
    zero_ratio: float,
) -> float:
    density_score = 1.0 - zero_ratio
    score = (
        (entropy_score * 0.34)
        + (spatial_frequency * 0.34)
        + (saturation_ratio * 0.18)
        + (density_score * 0.14)
    )
    return max(0.0, min(1.0, score))


def _build_python_profile(
    modality: ModalityKind,
    array: np.ndarray,
    max_risk: float,
    max_entropy: float,
    max_spatial_frequency: float,
    watch_margin: float,
    restricted_modalities: Sequence[ModalityKind],
) -> TensorInterceptProfile:
    flattened = array.reshape(array.shape[0], -1)
    finite_mask = np.isfinite(flattened)
    safe = np.where(finite_mask, flattened, 0.0)
    entropy_score = normalized_entropy(safe.reshape(-1))
    zero_ratio = float((np.abs(safe) < 1e-6).mean())
    spatial_frequency = _normalized_spatial_frequency(safe)
    saturation_ratio = _saturation_ratio(safe)
    risk_score = _risk_score(
        entropy_score=entropy_score,
        spatial_frequency=spatial_frequency,
        saturation_ratio=saturation_ratio,
        zero_ratio=zero_ratio,
    )

    notes: List[str] = []
    status = "ok"
    if entropy_score >= max_entropy:
        notes.append("Entropy is high enough that the tensor carries a dense signal field.")
        status = "watch"
    if spatial_frequency >= max_spatial_frequency:
        notes.append(
            "Spatial frequency is elevated, which often marks "
            "image- or waveform-heavy content."
        )
        status = "watch"
    if risk_score >= max_risk:
        notes.append("The combined geometric risk crossed the current intercept threshold.")
        status = "fail"
    elif risk_score >= max(max_risk - watch_margin, 0.0) and status == "ok":
        notes.append("The combined geometric risk is close to the configured intercept threshold.")
        status = "watch"
    if modality in restricted_modalities:
        notes.append("This modality is marked as restricted for the current request.")
        if status == "ok":
            status = "watch"

    return TensorInterceptProfile(
        modality=modality,
        batch_size=int(array.shape[0]),
        feature_width=int(flattened.shape[1]),
        entropy_score=entropy_score,
        spatial_frequency=spatial_frequency,
        saturation_ratio=saturation_ratio,
        zero_ratio=zero_ratio,
        risk_score=risk_score,
        status=status,
        notes=notes,
    )


def _profile_from_bridge(
    modality: ModalityKind,
    payload: Dict[str, Any],
    array: np.ndarray,
    settings: Settings,
    max_risk: float,
    max_entropy: float,
    max_spatial_frequency: float,
    watch_margin: float,
    restricted_modalities: Sequence[ModalityKind],
) -> TensorInterceptProfile:
    bridge = tensor_guard_from_payload(payload, settings)
    if bridge is None:
        return _build_python_profile(
            modality=modality,
            array=array,
            max_risk=max_risk,
            max_entropy=max_entropy,
            max_spatial_frequency=max_spatial_frequency,
            watch_margin=watch_margin,
            restricted_modalities=restricted_modalities,
        )

    notes = [str(item) for item in bridge.get("notes", [])]
    restriction_note = "This modality is marked as restricted for the current request."
    if modality in restricted_modalities and restriction_note not in notes:
        notes.append(restriction_note)
    return TensorInterceptProfile(
        modality=modality,
        batch_size=int(array.shape[0]),
        feature_width=int(array.reshape(array.shape[0], -1).shape[1]),
        entropy_score=float(bridge.get("entropy_score", 0.0)),
        spatial_frequency=float(bridge.get("spatial_frequency", 0.0)),
        saturation_ratio=float(bridge.get("saturation_ratio", 0.0)),
        zero_ratio=float(bridge.get("zero_ratio", 0.0)),
        risk_score=float(bridge.get("risk_score", 0.0)),
        status=str(bridge.get("status", "ok")),
        notes=notes,
    )


def build_tensor_intercept_response(
    request: InferenceRequest,
    settings: Settings,
) -> TensorInterceptResponse:
    arrays = arrays_from_request(request)
    metadata = request.metadata
    restricted_modalities = _restricted_modalities(metadata.get("restricted_modalities", []))
    max_risk = float(metadata.get("max_intercept_risk", settings.tensor_intercept_max_risk))
    max_entropy = float(
        metadata.get("max_intercept_entropy", settings.tensor_intercept_max_entropy)
    )
    max_spatial_frequency = float(
        metadata.get(
            "max_intercept_spatial_frequency",
            settings.tensor_intercept_max_spatial_frequency,
        )
    )
    watch_margin = float(
        metadata.get("intercept_watch_margin", settings.tensor_intercept_watch_margin)
    )

    enforce_requested = bool(metadata.get("block_tensor_intercept", False))
    policy_mode = str(
        metadata.get("tensor_intercept_mode", settings.tensor_intercept_default_mode)
    ).strip().lower()
    if enforce_requested or restricted_modalities:
        policy_mode = "enforce"
    if policy_mode not in {"observe", "enforce"}:
        policy_mode = settings.tensor_intercept_default_mode

    profiles = [
        _profile_from_bridge(
            modality=modality,  # type: ignore[arg-type]
            payload={
                **request.modalities[modality].model_dump(),
                "max_risk": max_risk,
                "max_entropy": max_entropy,
                "max_spatial_frequency": max_spatial_frequency,
                "watch_margin": watch_margin,
            },
            array=array,
            settings=settings,
            max_risk=max_risk,
            max_entropy=max_entropy,
            max_spatial_frequency=max_spatial_frequency,
            watch_margin=watch_margin,
            restricted_modalities=restricted_modalities,
        )
        for modality, array in sorted(arrays.items())
    ]

    triggered_modalities = [
        profile.modality
        for profile in profiles
        if profile.status == "fail"
        and (not restricted_modalities or profile.modality in restricted_modalities)
    ]
    blocked = policy_mode == "enforce" and bool(triggered_modalities)

    warnings: List[str] = []
    if blocked:
        warnings.append(
            "Inference was halted before fusion because the tensor intercept "
            "flagged restricted geometry in: "
            + ", ".join(triggered_modalities)
            + "."
        )
    elif any(profile.status == "fail" for profile in profiles):
        warnings.append(
            "One or more modalities crossed the geometric risk threshold, "
            "but the request is in observation mode."
        )
    elif any(profile.status == "watch" for profile in profiles):
        warnings.append(
            "A modality is nearing the current intercept threshold and "
            "deserves a narrower review lane."
        )

    return TensorInterceptResponse(
        request_id=str(metadata.get("request_id", request.model_id)),
        model_id=request.model_id,
        runtime_mode=request.runtime_mode,
        policy_mode=policy_mode,  # type: ignore[arg-type]
        restricted_modalities=restricted_modalities,
        blocked=blocked,
        triggered_modalities=triggered_modalities,
        intercept_profiles=profiles,
        warnings=warnings,
    )
