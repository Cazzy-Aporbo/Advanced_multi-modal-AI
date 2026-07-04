from __future__ import annotations

from ...contracts import IndustrialComplianceFinding
from .iec_61508 import evaluate_iec_61508
from .iso_13849 import evaluate_iso_13849
from .osha_1910 import evaluate_osha_1910


def evaluate_regulatory_posture(
    *, work_context, diagnoses
) -> tuple[list[IndustrialComplianceFinding], str]:
    findings: list[IndustrialComplianceFinding] = []
    findings.extend(evaluate_osha_1910(work_context=work_context, diagnoses=diagnoses))
    findings.extend(evaluate_iso_13849(work_context=work_context))
    findings.extend(evaluate_iec_61508(work_context=work_context, diagnoses=diagnoses))

    statuses = {item.status for item in findings}
    if "block" in statuses:
        return findings, "block"
    if "watch" in statuses or any(item.severity in {"high", "critical"} for item in diagnoses):
        return findings, "hold"
    return findings, "route"
