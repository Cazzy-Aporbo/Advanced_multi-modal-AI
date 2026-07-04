from __future__ import annotations

from ...contracts import IndustrialComplianceFinding, utc_now


def evaluate_iec_61508(*, work_context, diagnoses) -> list[IndustrialComplianceFinding]:
    findings: list[IndustrialComplianceFinding] = []
    highest_severity = max((item.severity for item in diagnoses), default="low")
    coverage_low = work_context.diagnostic_coverage_percent < 90.0

    if work_context.safety_function_proof_test_overdue and coverage_low:
        findings.append(
            IndustrialComplianceFinding(
                standard="IEC 61508",
                clause="7.4.9",
                status="block" if highest_severity in {"high", "critical"} else "watch",
                requirement=(
                    "Overdue proof testing and weak diagnostic coverage must "
                    "be cleared before safety claims are reused."
                ),
                evidence=[
                    f"safety_function_proof_test_overdue={work_context.safety_function_proof_test_overdue}",
                    f"diagnostic_coverage_percent={work_context.diagnostic_coverage_percent}",
                    f"highest_diagnosis_severity={highest_severity}",
                ],
                implication=(
                    "The safety function cannot be treated as fully "
                    "trustworthy until proof coverage is restored."
                ),
                checked_at=utc_now(),
            )
        )
    return findings
