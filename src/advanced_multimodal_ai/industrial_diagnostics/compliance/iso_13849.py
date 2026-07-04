from __future__ import annotations

from ...contracts import IndustrialComplianceFinding, utc_now


def evaluate_iso_13849(*, work_context) -> list[IndustrialComplianceFinding]:
    findings: list[IndustrialComplianceFinding] = []
    if not work_context.guard_interlock_verified:
        findings.append(
            IndustrialComplianceFinding(
                standard="ISO 13849-1",
                clause="6.2.6",
                status="block",
                requirement=(
                    "The protective guard path must be verified before " "restart or live motion."
                ),
                evidence=[f"guard_interlock_verified={work_context.guard_interlock_verified}"],
                implication="Restart remains blocked until the guard circuit is verified.",
                checked_at=utc_now(),
            )
        )
    if not work_context.manual_reset_verified:
        findings.append(
            IndustrialComplianceFinding(
                standard="ISO 13849-1",
                clause="5.2.2",
                status="watch",
                requirement=(
                    "A deliberate reset confirmation is required after the " "safeguarded stop."
                ),
                evidence=[f"manual_reset_verified={work_context.manual_reset_verified}"],
                implication=(
                    "The machine may not re-enter motion through an automatic " "restart path."
                ),
                checked_at=utc_now(),
            )
        )
    return findings
