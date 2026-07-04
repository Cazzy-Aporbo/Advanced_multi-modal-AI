from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

try:  # pragma: no cover - optional dependency
    import z3  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    z3 = None


Severity = str


@dataclass(frozen=True)
class DiagnosticRule:
    rule_id: str
    asset_kind: str
    component: str
    title: str
    severity: Severity
    conditions: tuple[tuple[str, str, float], ...]
    keywords: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    next_checks: tuple[str, ...]
    rationale: str


SEVERITY_WEIGHT: dict[Severity, float] = {
    "low": 0.18,
    "medium": 0.32,
    "high": 0.54,
    "critical": 0.72,
}

COMPARATORS: dict[str, Callable[[float, float], bool]] = {
    "<": lambda left, right: left < right,
    "<=": lambda left, right: left <= right,
    ">": lambda left, right: left > right,
    ">=": lambda left, right: left >= right,
}


RULES: tuple[DiagnosticRule, ...] = (
    DiagnosticRule(
        rule_id="diesel-lubrication-collapse",
        asset_kind="diesel_engine",
        component="lubrication",
        title="Lubrication collapse risk",
        severity="critical",
        conditions=(("oil_pressure_kpa", "<", 145.0), ("coolant_temp_c", ">", 102.0)),
        keywords=("stall", "knock", "oil"),
        blocked_actions=("restart", "continued_load"),
        next_checks=("inspect oil circuit", "sample bearing material", "verify relief valve"),
        rationale=(
            "Low oil pressure and rising coolant temperature usually travel together when "
            "lubrication loss begins to damage rotating surfaces."
        ),
    ),
    DiagnosticRule(
        rule_id="diesel-airpath-restriction",
        asset_kind="diesel_engine",
        component="air_path",
        title="Air-path restriction or boost collapse",
        severity="high",
        conditions=(("boost_pressure_kpa", "<", 110.0), ("exhaust_opacity_pct", ">", 68.0)),
        keywords=("smoke", "power", "surge"),
        blocked_actions=("full_throttle"),
        next_checks=(
            "inspect intake restriction",
            "check turbo actuation",
            "review injector balance",
        ),
        rationale=(
            "Weak boost and dark exhaust usually mean the engine is over-fueling relative "
            "to the air column actually reaching combustion."
        ),
    ),
    DiagnosticRule(
        rule_id="hydraulic-cavitation-window",
        asset_kind="hydraulic_system",
        component="pump_and_reservoir",
        title="Hydraulic cavitation window",
        severity="high",
        conditions=(("line_pressure_bar", "<", 145.0), ("fluid_temp_c", ">", 82.0)),
        keywords=("whine", "foam", "lag"),
        blocked_actions=("precision_lift", "pressure_hold"),
        next_checks=(
            "check suction restriction",
            "review reservoir level",
            "inspect relief chatter",
        ),
        rationale=(
            "Heat and weak line pressure together often point to suction starvation or a "
            "pump that is aerating the fluid column."
        ),
    ),
    DiagnosticRule(
        rule_id="hydraulic-contamination-escalation",
        asset_kind="hydraulic_system",
        component="fluid_cleanliness",
        title="Contamination escalation",
        severity="critical",
        conditions=(("contamination_iso_code", ">", 20.0), ("case_drain_flow_lpm", ">", 9.5)),
        keywords=("debris", "sticky", "grit"),
        blocked_actions=("continue_operation", "bypass_filter"),
        next_checks=("take oil sample", "inspect return filter", "check actuator scoring"),
        rationale=(
            "Dirty fluid and elevated case drain flow are strong early signals for internal "
            "wear that can quickly spread through the hydraulic loop."
        ),
    ),
    DiagnosticRule(
        rule_id="electrical-phase-loss",
        asset_kind="electrical_system",
        component="power_distribution",
        title="Phase loss or severe imbalance",
        severity="critical",
        conditions=(("line_voltage_v", "<", 400.0), ("current_imbalance_pct", ">", 10.0)),
        keywords=("trip", "brownout", "phase"),
        blocked_actions=("restart", "energize_drive"),
        next_checks=("measure phase continuity", "inspect contactors", "verify upstream feeder"),
        rationale=(
            "Undervoltage paired with large current imbalance usually means one phase is not "
            "sharing load correctly, which can damage motors quickly."
        ),
    ),
    DiagnosticRule(
        rule_id="electrical-insulation-breakdown",
        asset_kind="electrical_system",
        component="insulation_and_ground",
        title="Insulation breakdown risk",
        severity="high",
        conditions=(("insulation_resistance_mohm", "<", 1.0), ("winding_temp_c", ">", 120.0)),
        keywords=("ground", "burn", "odor"),
        blocked_actions=("energize_drive"),
        next_checks=("megger the winding", "inspect cable ingress", "dry and retest insulation"),
        rationale=(
            "Poor insulation and high winding temperature make a restart unsafe until the "
            "cause of the thermal rise is confirmed."
        ),
    ),
)


def list_supported_assets() -> list[str]:
    return sorted({rule.asset_kind for rule in RULES})


def diagnose_asset(
    *,
    asset_kind: str,
    sensor_values: Mapping[str, float],
    observation_terms: Iterable[str],
) -> list[dict[str, object]]:
    normalized_terms = {term.strip().lower() for term in observation_terms if term.strip()}
    diagnoses: list[dict[str, object]] = []
    for rule in RULES:
        if rule.asset_kind != asset_kind:
            continue
        condition_hits: list[str] = []
        for sensor_name, operator, threshold in rule.conditions:
            value = sensor_values.get(sensor_name)
            if value is None:
                break
            if not compare_signal(sensor_name, value, operator, threshold):
                break
            condition_hits.append(f"{sensor_name} {operator} {threshold:g} (observed {value:.3f})")
        else:
            keyword_hits = [keyword for keyword in rule.keywords if keyword in normalized_terms]
            if rule.keywords and not keyword_hits:
                continue
            confidence = min(
                0.54
                + (0.08 * len(condition_hits))
                + (0.04 * len(keyword_hits))
                + SEVERITY_WEIGHT[rule.severity],
                0.99,
            )
            diagnoses.append(
                {
                    "diagnosis_id": rule.rule_id,
                    "title": rule.title,
                    "component": rule.component,
                    "severity": rule.severity,
                    "confidence": round(confidence, 4),
                    "matched_signals": condition_hits,
                    "matched_observations": keyword_hits,
                    "blocked_actions": list(rule.blocked_actions),
                    "next_checks": list(rule.next_checks),
                    "rationale": rule.rationale,
                }
            )
    diagnoses.sort(
        key=lambda item: (
            SEVERITY_WEIGHT[str(item["severity"])],
            float(item["confidence"]),
        ),
        reverse=True,
    )
    return diagnoses


def compare_signal(sensor_name: str, value: float, operator: str, threshold: float) -> bool:
    comparator = COMPARATORS[operator]
    if z3 is None:
        return comparator(value, threshold)
    signal = z3.Real(sensor_name)
    solver = z3.Solver()
    solver.add(signal == z3.RealVal(str(value)))
    if operator == "<":
        solver.add(signal < threshold)
    elif operator == "<=":
        solver.add(signal <= threshold)
    elif operator == ">":
        solver.add(signal > threshold)
    else:
        solver.add(signal >= threshold)
    return solver.check() == z3.sat
