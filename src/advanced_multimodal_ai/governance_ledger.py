from __future__ import annotations

import base64
import hashlib
import json

from .contracts import ComplianceLedgerToken, RuntimeAttestationResponse

GOVERNANCE_SCOPE_RULES: tuple[tuple[str, str], ...] = (
    ("/v1/catalog", "catalog"),
    ("/v1/stewardship", "governance"),
    ("/v1/ontology", "governance"),
    ("/v1/bias", "governance"),
    ("/v1/privacy", "governance"),
    ("/v1/runtime", "runtime"),
    ("/v1/proof", "runtime"),
    ("/v1/readiness", "runtime"),
    ("/v1/repository", "runtime"),
    ("/v1/execution", "runtime"),
    ("/v1/infer", "inference"),
    ("/v1/data", "inference"),
    ("/v1/drift", "governance"),
    ("/v1/pipelines", "governance"),
    ("/v1/connectors", "governance"),
    ("/v1/jobs", "jobs"),
    ("/v1/research", "research"),
)

SCOPE_LANE_MAP: dict[str, list[str]] = {
    "catalog": ["dataset_catalog", "connector_ingest", "pipeline_ingest"],
    "governance": [
        "data_lifecycle",
        "change_control",
        "supply_chain_snapshot",
        "drift_baselines",
        "domain_ontology",
        "liability_surface",
        "bias_taxonomy",
        "privacy_membrane",
        "pipeline_export_replay",
    ],
    "runtime": [
        "readiness_report",
        "research_surfaces",
        "repository_pulse",
        "execution_journal",
    ],
    "inference": [
        "contract_inference",
        "research_bridge",
        "pipeline_export_replay",
    ],
    "jobs": ["video_cleanup", "contract_inference"],
    "research": ["research_surfaces", "research_bridge"],
}


def build_compliance_ledger_token(
    *,
    attestation: RuntimeAttestationResponse,
    route: str,
    method: str,
    status_code: int,
) -> ComplianceLedgerToken:
    scope = _governance_scope(route)
    governance_lanes = _governance_lanes(
        scope=scope,
        supported_lanes=attestation.supported_lanes,
    )
    payload = {
        "service": attestation.service,
        "version": attestation.version,
        "environment": attestation.environment,
        "method": method.upper(),
        "route": route,
        "status_code": int(status_code),
        "governance_scope": scope,
        "governance_lanes": governance_lanes,
        "openapi_sha256": attestation.openapi_sha256,
        "store_counts_hash": _stable_digest(attestation.store_counts),
        "issued_at": attestation.created_at,
    }
    compact_payload = _urlsafe_payload(payload)
    return ComplianceLedgerToken(
        token_id=_stable_digest(payload),
        service=attestation.service,
        version=attestation.version,
        environment=attestation.environment,
        method=method.upper(),
        route=route,
        status_code=int(status_code),
        governance_scope=scope,  # type: ignore[arg-type]
        governance_lanes=governance_lanes,
        openapi_sha256=attestation.openapi_sha256,
        store_counts_hash=payload["store_counts_hash"],
        issued_at=attestation.created_at,
        compact_payload=compact_payload,
    )


def _governance_scope(route: str) -> str:
    for prefix, scope in GOVERNANCE_SCOPE_RULES:
        if route.startswith(prefix):
            return scope
    return "runtime"


def _governance_lanes(*, scope: str, supported_lanes: list[str]) -> list[str]:
    lanes = SCOPE_LANE_MAP.get(scope, [])
    return [lane for lane in lanes if lane in supported_lanes]


def _stable_digest(payload: object) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _urlsafe_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(encoded.encode("utf-8")).decode("ascii").rstrip("=")
