from __future__ import annotations

from ...contracts import IndustrialInvariantResult, IndustrialModelCheckResponse, utc_now
from .formal_spec import ALLOWED_TRANSITIONS


def check_transition_trace(
    *, trace, work_context, compliance_findings
) -> IndustrialModelCheckResponse:
    blocked_transitions: list[str] = []
    invariants: list[IndustrialInvariantResult] = []

    for step in trace:
        allowed_next = ALLOWED_TRANSITIONS.get(step.from_state, set())
        if step.to_state not in allowed_next:
            blocked_transitions.append(
                f"{step.from_state} -> {step.to_state} is outside the declared transition set."
            )
        if step.to_state == "intervene" and not (step.lockout_applied and step.energy_isolated):
            blocked_transitions.append(
                "intervene requires lockout_applied=True and energy_isolated=True."
            )
        if step.to_state == "restart" and not (
            step.guard_interlock_verified
            and step.emergency_stop_verified
            and step.manual_reset_verified
        ):
            blocked_transitions.append(
                "restart requires guard, emergency stop, and manual reset verification."
            )

    blocking_findings = [item for item in compliance_findings if item.status == "block"]
    invariants.append(
        IndustrialInvariantResult(
            invariant_id="transition-graph-closed",
            description=(
                "Every state transition remains inside the declared " "diagnostic state graph."
            ),
            holds=all(
                step.to_state in ALLOWED_TRANSITIONS.get(step.from_state, set()) for step in trace
            ),
            evidence=[f"trace_length={len(trace)}"],
            checked_at=utc_now(),
        )
    )
    invariants.append(
        IndustrialInvariantResult(
            invariant_id="regulatory-blocks-stop-restart",
            description="A blocking regulatory finding prevents the trace from ending in restart.",
            holds=not (blocking_findings and any(step.to_state == "restart" for step in trace)),
            evidence=[
                f"blocking_findings={len(blocking_findings)}",
                f"restart_steps={sum(1 for step in trace if step.to_state == 'restart')}",
                f"restart_requested={work_context.restart_requested}",
            ],
            checked_at=utc_now(),
        )
    )

    return IndustrialModelCheckResponse(
        allowed=not blocked_transitions,
        blocked_transitions=blocked_transitions,
        invariants=invariants,
        evaluated_trace=list(trace),
    )
