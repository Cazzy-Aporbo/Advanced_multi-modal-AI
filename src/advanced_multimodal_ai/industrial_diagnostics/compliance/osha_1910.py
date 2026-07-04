from __future__ import annotations

from ...contracts import IndustrialComplianceFinding, utc_now


def evaluate_osha_1910(*, work_context, diagnoses) -> list[IndustrialComplianceFinding]:
    manual_intervention_required = any(item.blocked_actions for item in diagnoses)
    findings: list[IndustrialComplianceFinding] = []
    if manual_intervention_required and not (
        work_context.lockout_applied and work_context.energy_isolated
    ):
        findings.append(
            IndustrialComplianceFinding(
                standard="OSHA 1910",
                clause="1910.147",
                status="block",
                requirement=(
                    "Lockout and energy isolation must be established before "
                    "direct intervention."
                ),
                evidence=[
                    f"lockout_applied={work_context.lockout_applied}",
                    f"energy_isolated={work_context.energy_isolated}",
                ],
                implication=(
                    "Hands-on diagnostics cannot continue until hazardous " "energy is controlled."
                ),
                checked_at=utc_now(),
            )
        )
    elif manual_intervention_required:
        findings.append(
            IndustrialComplianceFinding(
                standard="OSHA 1910",
                clause="1910.147",
                status="pass",
                requirement="Hazardous energy remained isolated during the planned intervention.",
                evidence=[
                    f"lockout_applied={work_context.lockout_applied}",
                    f"energy_isolated={work_context.energy_isolated}",
                ],
                implication=(
                    "The field intervention may proceed inside a controlled "
                    "maintenance boundary."
                ),
                checked_at=utc_now(),
            )
        )
    return findings
