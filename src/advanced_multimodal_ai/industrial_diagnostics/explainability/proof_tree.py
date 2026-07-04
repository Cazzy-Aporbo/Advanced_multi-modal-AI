from __future__ import annotations

from ...contracts import IndustrialProofNode


def build_proof_tree(
    *, request, diagnoses, compliance_findings, invariants, verdict
) -> list[IndustrialProofNode]:
    nodes: list[IndustrialProofNode] = [
        IndustrialProofNode(
            node_id="root",
            parent_id="",
            label=f"{request.asset_kind} diagnostic chain",
            detail=(
                "Sensors, observations, compliance, and formal invariants "
                "are evaluated together."
            ),
            depth=0,
        ),
        IndustrialProofNode(
            node_id="sensors",
            parent_id="root",
            label="Sensor evidence",
            detail=f"{len(request.sensors)} sensor values were read for this diagnostic pass.",
            depth=1,
        ),
    ]
    for index, diagnosis in enumerate(diagnoses, start=1):
        nodes.append(
            IndustrialProofNode(
                node_id=f"diagnosis-{index}",
                parent_id="root",
                label=diagnosis.title,
                detail="; ".join(
                    [
                        *diagnosis.matched_signals,
                        *[f"observation={term}" for term in diagnosis.matched_observations],
                    ]
                )
                or diagnosis.rationale,
                depth=1,
            )
        )
    for index, finding in enumerate(compliance_findings, start=1):
        nodes.append(
            IndustrialProofNode(
                node_id=f"compliance-{index}",
                parent_id="root",
                label=f"{finding.standard} {finding.clause}",
                detail=finding.requirement,
                depth=1,
            )
        )
    for index, invariant in enumerate(invariants, start=1):
        nodes.append(
            IndustrialProofNode(
                node_id=f"invariant-{index}",
                parent_id="root",
                label=invariant.invariant_id,
                detail=f"{invariant.description} · holds={invariant.holds}",
                depth=1,
            )
        )
    nodes.append(
        IndustrialProofNode(
            node_id="verdict",
            parent_id="root",
            label="Final verdict",
            detail=f"Deterministic disposition: {verdict}.",
            depth=1,
        )
    )
    return nodes
