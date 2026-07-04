from __future__ import annotations

from typing import Iterable

from ..contracts import (
    IndustrialComplianceFinding,
    IndustrialDiagnosis,
    IndustrialDiagnosticRequest,
    IndustrialDiagnosticResponse,
    IndustrialInvariantResult,
    IndustrialModelCheckRequest,
    IndustrialModelCheckResponse,
    IndustrialScenarioBundle,
    IndustrialScenarioCard,
)
from .compliance import evaluate_regulatory_posture
from .deterministic_engine import (
    build_formal_trace,
    check_transition_trace,
    diagnose_asset,
    evaluate_formal_invariants,
)
from .explainability import build_audit_trail, build_fault_graph, build_proof_tree


def run_industrial_diagnostic(request: IndustrialDiagnosticRequest) -> IndustrialDiagnosticResponse:
    sensor_values = {item.sensor_id: item.value for item in request.sensors}
    observation_terms = _observation_terms(request)
    diagnosis_payloads = diagnose_asset(
        asset_kind=request.asset_kind,
        sensor_values=sensor_values,
        observation_terms=observation_terms,
    )
    diagnoses = [IndustrialDiagnosis.model_validate(item) for item in diagnosis_payloads]
    compliance_findings, verdict = evaluate_regulatory_posture(
        work_context=request.work_context,
        diagnoses=diagnoses,
    )
    trace = build_formal_trace(verdict=verdict, work_context=request.work_context)
    invariants = evaluate_formal_invariants(
        diagnoses=diagnoses,
        compliance_findings=compliance_findings,
        work_context=request.work_context,
        trace=trace,
    )
    if any(not item.holds for item in invariants):
        verdict = "block"
    proof_tree = build_proof_tree(
        request=request,
        diagnoses=diagnoses,
        compliance_findings=compliance_findings,
        invariants=invariants,
        verdict=verdict,
    )
    fault_graph = build_fault_graph(
        request=request,
        diagnoses=diagnoses,
        compliance_findings=compliance_findings,
        invariants=invariants,
        verdict=verdict,
    )
    audit_trail = build_audit_trail(
        request=request,
        diagnoses=diagnoses,
        compliance_findings=compliance_findings,
        invariants=invariants,
        verdict=verdict,
    )
    recommended_actions = _recommended_actions(diagnoses, compliance_findings, invariants)
    return IndustrialDiagnosticResponse(
        asset_kind=request.asset_kind,
        machine_family=request.machine_family,
        verdict=verdict,
        diagnoses=diagnoses,
        compliance_findings=compliance_findings,
        invariants=invariants,
        fault_graph=fault_graph,
        proof_tree=proof_tree,
        audit_trail=audit_trail,
        formal_trace=trace,
        recommended_actions=recommended_actions,
    )


def run_industrial_model_check(
    request: IndustrialModelCheckRequest,
) -> IndustrialModelCheckResponse:
    compliance_findings = [
        IndustrialComplianceFinding.model_validate(item) for item in request.compliance_findings
    ]
    return check_transition_trace(
        trace=request.trace,
        work_context=request.work_context,
        compliance_findings=compliance_findings,
    )


def list_industrial_scenarios() -> IndustrialScenarioBundle:
    return IndustrialScenarioBundle(
        scenarios=[
            IndustrialScenarioCard(
                scenario_id="diesel-engine-overheat-window",
                asset_kind="diesel_engine",
                label="Diesel engine overheat window",
                summary=(
                    "Pairs lubrication loss, thermal rise, and restart "
                    "restraint inside one deterministic pass."
                ),
                required_sensors=[
                    "oil_pressure_kpa",
                    "coolant_temp_c",
                    "boost_pressure_kpa",
                    "exhaust_opacity_pct",
                ],
                example_observations=["stall under load", "smoke pulse", "metallic knock"],
                expected_diagnosis_ids=[
                    "diesel-lubrication-collapse",
                    "diesel-airpath-restriction",
                ],
            ),
            IndustrialScenarioCard(
                scenario_id="hydraulic-cavitation-and-debris",
                asset_kind="hydraulic_system",
                label="Hydraulic cavitation and debris",
                summary=(
                    "Follows heat, contamination, and case drain flow before "
                    "the actuator loop is trusted again."
                ),
                required_sensors=[
                    "line_pressure_bar",
                    "fluid_temp_c",
                    "contamination_iso_code",
                    "case_drain_flow_lpm",
                ],
                example_observations=[
                    "whine at lift",
                    "foam in sight glass",
                    "sticky valve motion",
                ],
                expected_diagnosis_ids=[
                    "hydraulic-cavitation-window",
                    "hydraulic-contamination-escalation",
                ],
            ),
            IndustrialScenarioCard(
                scenario_id="electrical-phase-loss",
                asset_kind="electrical_system",
                label="Electrical phase loss and insulation drift",
                summary=(
                    "Separates power-distribution faults from insulation "
                    "decay before the drive is re-energized."
                ),
                required_sensors=[
                    "line_voltage_v",
                    "current_imbalance_pct",
                    "insulation_resistance_mohm",
                    "winding_temp_c",
                ],
                example_observations=["brownout", "ground odor", "repeated trip"],
                expected_diagnosis_ids=["electrical-phase-loss", "electrical-insulation-breakdown"],
            ),
        ]
    )


def build_industrial_diagnostic_proof() -> dict[str, object]:
    scenario_bundle = list_industrial_scenarios()
    sample_request = IndustrialDiagnosticRequest(
        asset_kind="diesel_engine",
        machine_family="field-diagnostics-reference",
        technician_report="Repeated stall under load with smoke pulse and a light metallic knock.",
        sensors=[
            {"sensor_id": "oil_pressure_kpa", "value": 112.0, "unit": "kPa"},
            {"sensor_id": "coolant_temp_c", "value": 108.4, "unit": "C"},
            {"sensor_id": "boost_pressure_kpa", "value": 101.0, "unit": "kPa"},
            {"sensor_id": "exhaust_opacity_pct", "value": 74.0, "unit": "%"},
        ],
        observations=[
            {
                "observation_id": "obs-1",
                "component": "engine",
                "symptom": "stall",
                "detail": "stall under load",
            },
            {
                "observation_id": "obs-2",
                "component": "exhaust",
                "symptom": "smoke",
                "detail": "dark smoke pulse",
            },
        ],
        work_context={
            "lockout_applied": False,
            "energy_isolated": False,
            "guard_interlock_verified": True,
            "emergency_stop_verified": True,
            "manual_reset_verified": False,
            "restart_requested": True,
            "safety_function_proof_test_overdue": True,
            "diagnostic_coverage_percent": 86.0,
        },
    )
    response = run_industrial_diagnostic(sample_request)
    return {
        "scenarios": scenario_bundle.model_dump(mode="json"),
        "sample_request": sample_request.model_dump(mode="json"),
        "sample_response": response.model_dump(mode="json"),
    }


def _observation_terms(request: IndustrialDiagnosticRequest) -> set[str]:
    terms = set(_tokenize(request.technician_report))
    for observation in request.observations:
        terms.update(_tokenize(observation.symptom))
        terms.update(_tokenize(observation.detail))
    return terms


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(character.lower() if character.isalnum() else " " for character in text)
    return [token for token in cleaned.split() if token]


def _recommended_actions(
    diagnoses: Iterable[IndustrialDiagnosis],
    compliance_findings: Iterable[IndustrialComplianceFinding],
    invariants: Iterable[IndustrialInvariantResult],
) -> list[str]:
    actions: list[str] = []
    for diagnosis in diagnoses:
        actions.extend(diagnosis.next_checks)
    for finding in compliance_findings:
        if finding.status in {"watch", "block"}:
            actions.append(f"{finding.standard} {finding.clause}: {finding.requirement}")
    for invariant in invariants:
        if not invariant.holds:
            actions.append(invariant.description)
    deduped: list[str] = []
    seen = set()
    for item in actions:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped[:12]
