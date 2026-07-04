from __future__ import annotations

from typing import Iterable

from ...contracts import IndustrialInvariantResult, IndustrialTransitionStep, utc_now

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "observe": {"isolate", "hold"},
    "isolate": {"verify", "hold"},
    "verify": {"intervene", "hold", "restart"},
    "intervene": {"verify", "hold", "restart"},
    "restart": {"observe", "hold"},
    "hold": {"observe", "isolate"},
}


def build_formal_trace(*, verdict: str, work_context) -> list[IndustrialTransitionStep]:
    trace = [
        IndustrialTransitionStep(
            from_state="observe",
            to_state="isolate",
            command="stabilize machine boundary",
            lockout_applied=work_context.lockout_applied,
            energy_isolated=work_context.energy_isolated,
            guard_interlock_verified=work_context.guard_interlock_verified,
            emergency_stop_verified=work_context.emergency_stop_verified,
            manual_reset_verified=work_context.manual_reset_verified,
            note="Begin by isolating the machine state before direct intervention.",
        ),
        IndustrialTransitionStep(
            from_state="isolate",
            to_state="verify",
            command="verify machine-safe state",
            lockout_applied=work_context.lockout_applied,
            energy_isolated=work_context.energy_isolated,
            guard_interlock_verified=work_context.guard_interlock_verified,
            emergency_stop_verified=work_context.emergency_stop_verified,
            manual_reset_verified=work_context.manual_reset_verified,
            note="Verification checks whether the machine is ready for direct work.",
        ),
    ]
    if verdict == "block":
        trace.append(
            IndustrialTransitionStep(
                from_state="verify",
                to_state="hold",
                command="hold machine until controls are complete",
                lockout_applied=work_context.lockout_applied,
                energy_isolated=work_context.energy_isolated,
                guard_interlock_verified=work_context.guard_interlock_verified,
                emergency_stop_verified=work_context.emergency_stop_verified,
                manual_reset_verified=work_context.manual_reset_verified,
                note="A blocking condition prevents restart or live intervention.",
            )
        )
    else:
        trace.append(
            IndustrialTransitionStep(
                from_state="verify",
                to_state="intervene",
                command="perform bounded diagnostic intervention",
                lockout_applied=work_context.lockout_applied,
                energy_isolated=work_context.energy_isolated,
                guard_interlock_verified=work_context.guard_interlock_verified,
                emergency_stop_verified=work_context.emergency_stop_verified,
                manual_reset_verified=work_context.manual_reset_verified,
                note="The intervention step stays bounded by lockout and verification state.",
            )
        )
        trace.append(
            IndustrialTransitionStep(
                from_state="intervene",
                to_state="restart",
                command="restart only after guards and reset are verified",
                lockout_applied=work_context.lockout_applied,
                energy_isolated=work_context.energy_isolated,
                guard_interlock_verified=work_context.guard_interlock_verified,
                emergency_stop_verified=work_context.emergency_stop_verified,
                manual_reset_verified=work_context.manual_reset_verified,
                note="Restart remains conditional on protective controls.",
            )
        )
    return trace


def evaluate_formal_invariants(
    *,
    diagnoses: Iterable,
    compliance_findings: Iterable,
    work_context,
    trace: list[IndustrialTransitionStep],
) -> list[IndustrialInvariantResult]:
    diagnosis_list = list(diagnoses)
    finding_list = list(compliance_findings)
    critical_present = any(item.severity == "critical" for item in diagnosis_list)
    blocking_finding_present = any(item.status == "block" for item in finding_list)
    manual_intervention_required = any(item.blocked_actions for item in diagnosis_list)
    return [
        IndustrialInvariantResult(
            invariant_id="lockout-before-intervention",
            description="Manual intervention requires both lockout and verified energy isolation.",
            holds=(
                not manual_intervention_required
                or (work_context.lockout_applied and work_context.energy_isolated)
            ),
            evidence=[
                f"lockout_applied={work_context.lockout_applied}",
                f"energy_isolated={work_context.energy_isolated}",
                f"trace_length={len(trace)}",
            ],
            checked_at=utc_now(),
        ),
        IndustrialInvariantResult(
            invariant_id="restart-after-protective-controls",
            description=(
                "Restart cannot proceed without guard, emergency stop, and "
                "manual reset verification."
            ),
            holds=(
                not work_context.restart_requested
                or (
                    work_context.guard_interlock_verified
                    and work_context.emergency_stop_verified
                    and work_context.manual_reset_verified
                )
            ),
            evidence=[
                f"restart_requested={work_context.restart_requested}",
                f"guard_interlock_verified={work_context.guard_interlock_verified}",
                f"manual_reset_verified={work_context.manual_reset_verified}",
            ],
            checked_at=utc_now(),
        ),
        IndustrialInvariantResult(
            invariant_id="critical-faults-do-not-route",
            description=(
                "A critical diagnosis or a blocking regulatory finding " "prevents a route verdict."
            ),
            holds=not (critical_present or blocking_finding_present),
            evidence=[
                f"critical_present={critical_present}",
                f"blocking_finding_present={blocking_finding_present}",
            ],
            checked_at=utc_now(),
        ),
    ]
