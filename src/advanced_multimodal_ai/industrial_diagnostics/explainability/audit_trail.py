from __future__ import annotations

import hashlib
import json
from typing import Any

from ...contracts import IndustrialAuditEntry, utc_now


def build_audit_trail(
    *, request, diagnoses, compliance_findings, invariants, verdict
) -> list[IndustrialAuditEntry]:
    rows = [
        ("request", request.model_dump(mode="json")),
        (
            "diagnoses",
            [item.model_dump(mode="json") for item in diagnoses],
        ),
        (
            "compliance",
            [item.model_dump(mode="json") for item in compliance_findings],
        ),
        (
            "invariants",
            [item.model_dump(mode="json") for item in invariants],
        ),
        ("verdict", {"verdict": verdict}),
    ]
    parent_hash = ""
    entries: list[IndustrialAuditEntry] = []
    for index, (label, payload) in enumerate(rows, start=1):
        entry_hash = _hash_payload({"label": label, "payload": payload, "parent_hash": parent_hash})
        entries.append(
            IndustrialAuditEntry(
                entry_id=f"audit-{index:02d}",
                label=label,
                parent_hash=parent_hash,
                sha256=entry_hash,
                recorded_at=utc_now(),
                note=f"{label} sealed into the industrial diagnostic chain.",
            )
        )
        parent_hash = entry_hash
    return entries


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
