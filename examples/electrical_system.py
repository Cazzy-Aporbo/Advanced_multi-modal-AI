from __future__ import annotations

import json

from advanced_multimodal_ai.contracts import IndustrialDiagnosticRequest
from advanced_multimodal_ai.industrial_diagnostics import run_industrial_diagnostic


request = IndustrialDiagnosticRequest(
    asset_kind="electrical_system",
    machine_family="motor-control-reference",
    technician_report="Repeated trip after a brownout with a hot winding smell.",
    sensors=[
        {"sensor_id": "line_voltage_v", "value": 388.0, "unit": "V"},
        {"sensor_id": "current_imbalance_pct", "value": 11.8, "unit": "%"},
        {"sensor_id": "insulation_resistance_mohm", "value": 0.82, "unit": "MOhm"},
        {"sensor_id": "winding_temp_c", "value": 128.0, "unit": "C"},
    ],
    observations=[
        {"component": "drive", "symptom": "brownout", "detail": "voltage dip before trip"},
        {"component": "cabinet", "symptom": "odor", "detail": "warm winding odor"},
    ],
    work_context={
        "lockout_applied": True,
        "energy_isolated": True,
        "guard_interlock_verified": False,
        "emergency_stop_verified": True,
        "manual_reset_verified": False,
        "restart_requested": True,
    },
)

print(json.dumps(run_industrial_diagnostic(request).model_dump(mode="json"), indent=2))
