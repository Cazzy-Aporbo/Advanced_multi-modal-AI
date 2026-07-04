from __future__ import annotations

from collections import defaultdict

from ...contracts import (
    IndustrialComplianceFinding,
    IndustrialDiagnosis,
    IndustrialDiagnosticRequest,
    IndustrialFaultGraph,
    IndustrialFaultGraphEdge,
    IndustrialFaultGraphNode,
    IndustrialInvariantResult,
)


def build_fault_graph(
    *,
    request: IndustrialDiagnosticRequest,
    diagnoses: list[IndustrialDiagnosis],
    compliance_findings: list[IndustrialComplianceFinding],
    invariants: list[IndustrialInvariantResult],
    verdict: str,
) -> IndustrialFaultGraph:
    nodes: dict[str, IndustrialFaultGraphNode] = {}
    edges: list[IndustrialFaultGraphEdge] = []

    def add_node(node: IndustrialFaultGraphNode) -> None:
        nodes.setdefault(node.node_id, node)

    def add_edge(source: str, target: str, relation: str, evidence: str = "") -> None:
        edge_id = f"{source}->{target}:{relation}"
        edges.append(
            IndustrialFaultGraphEdge(
                edge_id=edge_id,
                source=source,
                target=target,
                relation=relation,
                evidence=evidence,
            )
        )

    sensor_node_ids: dict[str, str] = {}
    for sensor in request.sensors:
        node_id = f"sensor:{sensor.sensor_id}"
        sensor_node_ids[sensor.sensor_id] = node_id
        add_node(
            IndustrialFaultGraphNode(
                node_id=node_id,
                kind="sensor",
                label=sensor.sensor_id,
                detail=f"{sensor.value:.3f} {sensor.unit}".strip(),
                metrics={"value": sensor.value, "unit": sensor.unit},
            )
        )

    observation_node_ids: dict[int, str] = {}
    observation_terms: dict[int, set[str]] = {}
    for index, observation in enumerate(request.observations):
        node_id = f"observation:{index}"
        observation_node_ids[index] = node_id
        terms = _token_set(
            " ".join([observation.component, observation.symptom, observation.detail])
        )
        observation_terms[index] = terms
        add_node(
            IndustrialFaultGraphNode(
                node_id=node_id,
                kind="observation",
                label=observation.symptom,
                detail=observation.detail or observation.component,
                metrics={"component": observation.component},
            )
        )

    verdict_node_id = f"verdict:{verdict}"
    add_node(
        IndustrialFaultGraphNode(
            node_id=verdict_node_id,
            kind="verdict",
            label=verdict,
            detail="Final routing posture after deterministic diagnosis and safety review.",
            severity="critical" if verdict == "block" else ("high" if verdict == "hold" else "low"),
            state=verdict,
        )
    )

    action_node_ids: dict[str, str] = {}
    blocked_action_sources: defaultdict[str, list[str]] = defaultdict(list)

    sorted_diagnoses = sorted(
        diagnoses,
        key=lambda item: (_severity_rank(item.severity), item.confidence),
        reverse=True,
    )

    primary_path: list[str] = []
    primary_diagnosis_id = ""
    primary_compliance_id = ""
    primary_action_id = ""

    for diagnosis in sorted_diagnoses:
        diagnosis_node_id = f"diagnosis:{diagnosis.diagnosis_id}"
        add_node(
            IndustrialFaultGraphNode(
                node_id=diagnosis_node_id,
                kind="diagnosis",
                label=diagnosis.title,
                detail=diagnosis.rationale,
                severity=diagnosis.severity,
                metrics={"confidence": diagnosis.confidence, "component": diagnosis.component},
            )
        )

        matched_sensor_names = [_sensor_name_from_match(item) for item in diagnosis.matched_signals]
        for sensor_name, evidence in zip(
            matched_sensor_names, diagnosis.matched_signals, strict=False
        ):
            sensor_node_id = sensor_node_ids.get(sensor_name)
            if sensor_node_id:
                add_edge(sensor_node_id, diagnosis_node_id, "threshold_trip", evidence)

        matched_keywords = set(diagnosis.matched_observations)
        for index, terms in observation_terms.items():
            overlap = sorted(matched_keywords & terms)
            if overlap:
                add_edge(
                    observation_node_ids[index],
                    diagnosis_node_id,
                    "symptom_match",
                    ", ".join(overlap),
                )

        for blocked_action in diagnosis.blocked_actions:
            action_node_id = action_node_ids.setdefault(blocked_action, f"action:{blocked_action}")
            add_node(
                IndustrialFaultGraphNode(
                    node_id=action_node_id,
                    kind="action",
                    label=blocked_action.replace("_", " "),
                    detail="Action restricted until the signal chain is resolved.",
                    severity=diagnosis.severity,
                )
            )
            blocked_action_sources[blocked_action].append(diagnosis.diagnosis_id)
            add_edge(
                diagnosis_node_id,
                action_node_id,
                "blocks_action",
                diagnosis.diagnosis_id,
            )
            add_edge(action_node_id, verdict_node_id, "constrains_verdict", verdict)
            if not primary_action_id:
                primary_action_id = action_node_id

        if not primary_diagnosis_id:
            primary_diagnosis_id = diagnosis_node_id

    for index, finding in enumerate(compliance_findings):
        node_id = f"compliance:{index}"
        add_node(
            IndustrialFaultGraphNode(
                node_id=node_id,
                kind="compliance",
                label=f"{finding.standard} {finding.clause}",
                detail=finding.requirement,
                severity=finding.status,
                state=finding.status,
                metrics={"checked_at": finding.checked_at},
            )
        )

        linked = False
        lower_requirement = finding.requirement.lower()
        lower_evidence = " ".join(finding.evidence).lower()
        for blocked_action, _diagnosis_ids in blocked_action_sources.items():
            action_label = blocked_action.replace("_", " ")
            if action_label in lower_requirement or blocked_action in lower_evidence:
                action_node_id = action_node_ids[blocked_action]
                add_edge(action_node_id, node_id, "regulated_by", finding.status)
                linked = True
        if not linked and primary_diagnosis_id:
            add_edge(primary_diagnosis_id, node_id, "requires_control", finding.status)
        add_edge(node_id, verdict_node_id, "influences_verdict", finding.status)
        if not primary_compliance_id and finding.status in {"block", "watch"}:
            primary_compliance_id = node_id

    for invariant in invariants:
        node_id = f"invariant:{invariant.invariant_id}"
        add_node(
            IndustrialFaultGraphNode(
                node_id=node_id,
                kind="invariant",
                label=invariant.invariant_id,
                detail=invariant.description,
                severity="watch" if invariant.holds else "block",
                state="holds" if invariant.holds else "violated",
                metrics={"evidence_count": len(invariant.evidence)},
            )
        )
        if primary_compliance_id:
            add_edge(primary_compliance_id, node_id, "validated_by", invariant.invariant_id)
        elif primary_diagnosis_id:
            add_edge(primary_diagnosis_id, node_id, "validated_by", invariant.invariant_id)
        add_edge(node_id, verdict_node_id, "finalizes_verdict", invariant.invariant_id)

    primary_path.extend(
        [
            node_id
            for node_id in [
                _first_sensor_for_primary(primary_diagnosis_id, edges),
                primary_diagnosis_id,
                primary_compliance_id,
                primary_action_id,
                verdict_node_id,
            ]
            if node_id
        ]
    )

    return IndustrialFaultGraph(nodes=list(nodes.values()), edges=edges, primary_path=primary_path)


def _token_set(text: str) -> set[str]:
    cleaned = "".join(character.lower() if character.isalnum() else " " for character in text)
    return {token for token in cleaned.split() if token}


def _sensor_name_from_match(match_text: str) -> str:
    return match_text.split(" ", 1)[0].strip()


def _first_sensor_for_primary(
    primary_diagnosis_id: str,
    edges: list[IndustrialFaultGraphEdge],
) -> str:
    if not primary_diagnosis_id:
        return ""
    for edge in edges:
        if edge.target == primary_diagnosis_id and edge.source.startswith("sensor:"):
            return edge.source
    return ""


def _severity_rank(severity: str) -> int:
    order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return order.get(severity, 0)
