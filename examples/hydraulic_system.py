from __future__ import annotations

import json

from advanced_multimodal_ai.contracts import IndustrialDiagnosticRequest
from advanced_multimodal_ai.industrial_diagnostics import run_industrial_diagnostic


request = IndustrialDiagnosticRequest(
    asset_kind="hydraulic_system",
    machine_family="hydraulic-reference-loop",
    technician_report="Lift is lagging, the reservoir is foaming, and the valve motion feels sticky.",
    sensors=[
        {"sensor_id": "line_pressure_bar", "value": 131.0, "unit": "bar"},
        {"sensor_id": "fluid_temp_c", "value": 87.0, "unit": "C"},
        {"sensor_id": "contamination_iso_code", "value": 22.0, "unit": "code"},
        {"sensor_id": "case_drain_flow_lpm", "value": 10.4, "unit": "lpm"},
    ],
    observations=[
        {"component": "pump", "symptom": "whine", "detail": "high-pitch whine at lift"},
        {"component": "reservoir", "symptom": "foam", "detail": "foam visible in sight glass"},
    ],
    work_context={
        "lockout_applied": True,
        "energy_isolated": True,
        "guard_interlock_verified": True,
        "emergency_stop_verified": True,
        "manual_reset_verified": True,
        "restart_requested": False,
    },
)

print(json.dumps(run_industrial_diagnostic(request).model_dump(mode="json"), indent=2))
