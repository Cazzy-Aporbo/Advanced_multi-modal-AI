from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Dict, List

from .contracts import (
    ApiTraceRecord,
    GeometricConstraint,
    LiabilityGap,
    LiabilitySurfaceResponse,
    OntologySnapshot,
)


def surface_operational_liability(
    snapshot: OntologySnapshot,
    traces: List[ApiTraceRecord],
) -> LiabilitySurfaceResponse:
    heatmap: List[LiabilityGap] = []
    route_scores: Dict[str, List[float]] = defaultdict(list)
    proposed_patches: List[str] = []
    blocked_routes = set()

    for trace in traces:
        applicable = [
            constraint
            for constraint in snapshot.constraints
            if _constraint_applies(constraint, trace)
        ]
        violations = [
            constraint
            for constraint in applicable
            if _trace_violates_constraint(constraint, trace)
        ]
        if not violations:
            continue

        severity = _severity_from_constraints(violations)
        findings = [_describe_violation(constraint, trace) for constraint in violations]
        patch = _proposed_patch(violations[0], trace)
        gap = LiabilityGap(
            trace_id=trace.trace_id,
            route=trace.route,
            severity=severity,
            violated_constraints=[constraint.policy_name for constraint in violations],
            findings=findings,
            proposed_patch=patch,
        )
        heatmap.append(gap)
        route_scores[trace.route].append(_severity_score(severity))
        proposed_patches.append(patch)
        if severity == "high":
            blocked_routes.add(trace.route)

    return LiabilitySurfaceResponse(
        snapshot_id=snapshot.snapshot_id,
        blocked_routes=sorted(blocked_routes),
        route_scores={route: float(mean(scores)) for route, scores in route_scores.items()},
        heatmap=heatmap,
        proposed_patches=_dedupe_keep_order(proposed_patches),
    )


def _constraint_applies(constraint: GeometricConstraint, trace: ApiTraceRecord) -> bool:
    subject_matches = constraint.subject == trace.route or constraint.subject in trace.route
    if constraint.data_categories:
        category_matches = any(
            category.lower() in {value.lower() for value in trace.data_categories}
            for category in constraint.data_categories
        )
        return subject_matches or category_matches
    return subject_matches


def _trace_violates_constraint(
    constraint: GeometricConstraint,
    trace: ApiTraceRecord,
) -> bool:
    source_zone = _region_to_zone(trace.source_region)
    destination_zone = _region_to_zone(trace.destination_region)

    if constraint.action == "require_encryption":
        return not trace.transport_encrypted
    if constraint.action == "require_review":
        return not bool(trace.metadata.get("reviewed", False))
    if constraint.action == "block":
        return (
            (not constraint.from_zone or constraint.from_zone == source_zone)
            and (not constraint.to_zone or constraint.to_zone == destination_zone)
        )
    if constraint.action == "pin_region":
        return bool(constraint.to_zone) and destination_zone != constraint.to_zone
    return False


def _describe_violation(constraint: GeometricConstraint, trace: ApiTraceRecord) -> str:
    if constraint.action == "require_encryption":
        return f"{trace.route} moved governed data without an encrypted transport lane."
    if constraint.action == "require_review":
        return (
            f"{trace.route} executed without the reviewed approval lane "
            "described in the source artifact."
        )
    if constraint.action == "block":
        return (
            f"{trace.route} crossed from {trace.source_region or 'unknown'} to "
            f"{trace.destination_region or 'unknown'} against the declared transfer boundary."
        )
    if constraint.action == "pin_region":
        return (
            f"{trace.route} landed in {trace.destination_region or 'unknown'} "
            f"outside the allowed care or residence region."
        )
    return f"{trace.route} violated {constraint.policy_name}."


def _proposed_patch(constraint: GeometricConstraint, trace: ApiTraceRecord) -> str:
    if constraint.action == "require_encryption":
        return (
            f"Require encrypted transport for {trace.route} "
            "before the payload leaves the caller."
        )
    if constraint.action == "require_review":
        return f"Move {trace.route} behind a reviewed governance queue before execution."
    if constraint.action == "block":
        return f"Reroute {trace.route} into a protected enclave and stop the blocked transfer path."
    if constraint.action == "pin_region":
        return f"Re-pin {trace.route} to {constraint.to_zone} and reject off-region destinations."
    return f"Review {trace.route} against {constraint.policy_name}."


def _severity_from_constraints(constraints: List[GeometricConstraint]) -> str:
    if any(constraint.action in {"block", "pin_region"} for constraint in constraints):
        return "high"
    if any(constraint.action == "require_encryption" for constraint in constraints):
        return "medium"
    return "low"


def _severity_score(severity: str) -> float:
    return {"low": 0.33, "medium": 0.66, "high": 1.0}[severity]


def _region_to_zone(region: str) -> str:
    normalized = region.strip().lower()
    return f"zone::{normalized}" if normalized else ""


def _dedupe_keep_order(values: List[str]) -> List[str]:
    seen: Dict[str, None] = {}
    return [seen.setdefault(value, None) or value for value in values if value not in seen]
