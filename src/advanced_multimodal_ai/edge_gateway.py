from __future__ import annotations

import hashlib
import json
from typing import Iterable

import numpy as np

from .contracts import (
    EdgeGatewayPolicy,
    EdgePacketEvaluationResponse,
    EdgePacketMetric,
    EdgePacketRequest,
    EdgeRouteAction,
    EdgeTrackingLedgerEntry,
)
from .signal_math import normalized_entropy

POLICY_PROFILES: dict[str, EdgeGatewayPolicy] = {
    "EU_EEA": EdgeGatewayPolicy(
        jurisdiction="EU_EEA",
        max_entropy_limit=0.86,
        max_zero_ratio=0.72,
        min_finite_ratio=0.995,
        allow_cross_border=False,
        require_encryption=True,
        detail=(
            "EU_EEA packets stay local by default, require encrypted transport, "
            "and slow down when modality geometry becomes too unstable."
        ),
    ),
    "US_GLOBAL": EdgeGatewayPolicy(
        jurisdiction="US_GLOBAL",
        max_entropy_limit=0.92,
        max_zero_ratio=0.78,
        min_finite_ratio=0.99,
        allow_cross_border=True,
        require_encryption=True,
        detail=(
            "US_GLOBAL keeps transport encrypted but permits cross-border routing "
            "when the packet geometry remains inside the live policy window."
        ),
    ),
    "APAC_REGIONAL": EdgeGatewayPolicy(
        jurisdiction="APAC_REGIONAL",
        max_entropy_limit=0.88,
        max_zero_ratio=0.75,
        min_finite_ratio=0.992,
        allow_cross_border=False,
        require_encryption=True,
        detail=(
            "APAC_REGIONAL favors in-region routing and holds packets when sparse "
            "or degenerate geometry makes downstream reuse harder to trust."
        ),
    ),
}


def evaluate_edge_packet(
    request: EdgePacketRequest,
    *,
    parent_hash: str = "",
) -> EdgePacketEvaluationResponse:
    policy = POLICY_PROFILES[request.jurisdiction]
    metrics = [
        _build_metric(modality=modality, values=payload.values)
        for modality, payload in request.modalities.items()
    ]
    cross_border = request.source_region.strip().upper() != request.target_region.strip().upper()
    overall_entropy_score = float(np.mean([metric.entropy_score for metric in metrics]))
    highest_modality_risk = min(
        max(_metric_risk(metric, policy) for metric in metrics),
        1.0,
    )
    notes = _build_notes(
        request=request,
        policy=policy,
        metrics=metrics,
        cross_border=cross_border,
    )
    action = _route_action(
        request=request,
        policy=policy,
        metrics=metrics,
        cross_border=cross_border,
    )
    manifest_hash = _stable_digest(
        {
            "transaction_id": request.transaction_id,
            "connector_kind": request.connector_kind,
            "modality_hashes": [metric.signature_sha256 for metric in metrics],
        }
    )
    ledger_entry = _build_ledger_entry(
        request=request,
        action=action,
        manifest_hash=manifest_hash,
        overall_entropy_score=overall_entropy_score,
        highest_modality_risk=highest_modality_risk,
        cross_border=cross_border,
        notes=notes,
        parent_hash=parent_hash,
    )
    return EdgePacketEvaluationResponse(
        transaction_id=request.transaction_id,
        route_action=action,
        authorized_for_execution=action == "route",
        jurisdiction=request.jurisdiction,
        cross_border=cross_border,
        manifest_hash=manifest_hash,
        overall_entropy_score=overall_entropy_score,
        highest_modality_risk=highest_modality_risk,
        metrics=metrics,
        notes=notes,
        active_policy=policy,
        ledger_entry=ledger_entry,
    )


def _build_metric(*, modality: str, values: Iterable[float]) -> EdgePacketMetric:
    array = np.asarray(list(values), dtype=np.float32).reshape(-1)
    finite_mask = np.isfinite(array)
    finite_values = array[finite_mask]
    finite_ratio = float(finite_mask.mean()) if array.size else 1.0
    zero_ratio = float((np.abs(finite_values) < 1.0e-6).mean()) if finite_values.size else 1.0
    rms_level = (
        float(np.sqrt(np.mean(np.square(finite_values, dtype=np.float64))))
        if finite_values.size
        else 0.0
    )
    entropy_score = normalized_entropy(finite_values) if finite_values.size else 0.0
    signature_sha256 = hashlib.sha256(finite_values.tobytes()).hexdigest()
    return EdgePacketMetric(
        modality=modality,
        entropy_score=entropy_score,
        zero_ratio=zero_ratio,
        finite_ratio=finite_ratio,
        rms_level=rms_level,
        sample_size=max(1, int(array.size)),
        signature_sha256=signature_sha256,
    )


def _metric_risk(metric: EdgePacketMetric, policy: EdgeGatewayPolicy) -> float:
    return max(
        metric.entropy_score / max(policy.max_entropy_limit, 1.0e-6),
        metric.zero_ratio / max(policy.max_zero_ratio, 1.0e-6),
        (1.0 - metric.finite_ratio) / max(1.0 - policy.min_finite_ratio, 1.0e-6),
    )


def _route_action(
    *,
    request: EdgePacketRequest,
    policy: EdgeGatewayPolicy,
    metrics: list[EdgePacketMetric],
    cross_border: bool,
) -> EdgeRouteAction:
    if policy.require_encryption and not request.encrypted_in_transit:
        return "block"
    if cross_border and not policy.allow_cross_border:
        return "block"
    if any(metric.finite_ratio < policy.min_finite_ratio for metric in metrics):
        return "block"
    if any(metric.entropy_score > policy.max_entropy_limit for metric in metrics):
        return "hold"
    if any(metric.zero_ratio > policy.max_zero_ratio for metric in metrics):
        return "hold"
    return "route"


def _build_notes(
    *,
    request: EdgePacketRequest,
    policy: EdgeGatewayPolicy,
    metrics: list[EdgePacketMetric],
    cross_border: bool,
) -> list[str]:
    notes = [
        f"policy={policy.jurisdiction}",
        f"connector_kind={request.connector_kind or 'direct'}",
        f"modalities={','.join(metric.modality for metric in metrics)}",
    ]
    if cross_border:
        notes.append(f"cross_border={request.source_region}->{request.target_region}")
    if policy.require_encryption and not request.encrypted_in_transit:
        notes.append("blocked: encrypted transport is required for this jurisdiction.")
    if cross_border and not policy.allow_cross_border:
        notes.append("blocked: policy keeps this packet in-region.")
    for metric in metrics:
        if metric.finite_ratio < policy.min_finite_ratio:
            notes.append(f"{metric.modality}: finite ratio fell below live policy.")
        if metric.entropy_score > policy.max_entropy_limit:
            notes.append(f"{metric.modality}: entropy crossed the hold threshold.")
        if metric.zero_ratio > policy.max_zero_ratio:
            notes.append(
                f"{metric.modality}: zero-heavy geometry suggests padding or dead signal."
            )
    if len(notes) == 3:
        notes.append("packet geometry stayed inside the active live policy window.")
    return notes


def _build_ledger_entry(
    *,
    request: EdgePacketRequest,
    action: EdgeRouteAction,
    manifest_hash: str,
    overall_entropy_score: float,
    highest_modality_risk: float,
    cross_border: bool,
    notes: list[str],
    parent_hash: str,
) -> EdgeTrackingLedgerEntry:
    payload = {
        "transaction_id": request.transaction_id,
        "jurisdiction": request.jurisdiction,
        "source_region": request.source_region,
        "target_region": request.target_region,
        "route_action": action,
        "manifest_hash": manifest_hash,
        "overall_entropy_score": round(overall_entropy_score, 6),
        "highest_modality_risk": round(highest_modality_risk, 6),
        "encrypted_in_transit": request.encrypted_in_transit,
        "cross_border": cross_border,
        "connector_kind": request.connector_kind,
        "notes": notes,
        "ledger_parent_hash": parent_hash,
    }
    ledger_hash = _stable_digest(payload)
    return EdgeTrackingLedgerEntry(
        transaction_id=request.transaction_id,
        jurisdiction=request.jurisdiction,
        source_region=request.source_region,
        target_region=request.target_region,
        route_action=action,
        manifest_hash=manifest_hash,
        overall_entropy_score=overall_entropy_score,
        highest_modality_risk=min(highest_modality_risk, 1.0),
        encrypted_in_transit=request.encrypted_in_transit,
        cross_border=cross_border,
        connector_kind=request.connector_kind,
        ledger_parent_hash=parent_hash,
        ledger_hash=ledger_hash,
        notes=notes,
    )


def _stable_digest(payload: object) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
