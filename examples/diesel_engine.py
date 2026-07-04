from __future__ import annotations

import json

from advanced_multimodal_ai.contracts import IndustrialDiagnosticRequest
from advanced_multimodal_ai.industrial_diagnostics import run_industrial_diagnostic


request = IndustrialDiagnosticRequest(
    asset_kind="diesel_engine",
    machine_family="diesel-reference-rig",
    technician_report="Repeated stall under load with a smoke pulse and metallic knock.",
    sensors=[
        {"sensor_id": "oil_pressure_kpa", "value": 112.0, "unit": "kPa"},
        {"sensor_id": "coolant_temp_c", "value": 108.4, "unit": "C"},
        {"sensor_id": "boost_pressure_kpa", "value": 101.0, "unit": "kPa"},
        {"sensor_id": "exhaust_opacity_pct", "value": 74.0, "unit": "%"},
    ],
    observations=[
        {"component": "engine", "symptom": "stall", "detail": "stall under load"},
        {"component": "exhaust", "symptom": "smoke", "detail": "dark smoke pulse"},
    ],
    work_context={
        "lockout_applied": False,
        "energy_isolated": False,
        "guard_interlock_verified": True,
        "emergency_stop_verified": True,
        "manual_reset_verified": False,
        "restart_requested": True,
    },
)

print(json.dumps(run_industrial_diagnostic(request).model_dump(mode="json"), indent=2))
