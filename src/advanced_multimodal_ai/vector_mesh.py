from __future__ import annotations

from typing import get_args

from .config import Settings
from .contracts import ConnectorKind, EdgeGatewayPolicy, EdgeGatewayTopology


def build_edge_gateway_topology(
    *,
    settings: Settings,
    route_count: int,
    ledger_event_count: int,
    store_counts: dict[str, int],
    active_policy: EdgeGatewayPolicy,
) -> EdgeGatewayTopology:
    return EdgeGatewayTopology(
        service=settings.service_name,
        version=settings.service_version,
        route_count=route_count,
        ledger_event_count=ledger_event_count,
        retrieval_backend=settings.retrieval_backend,
        active_policy=active_policy,
        connector_kinds=list(get_args(ConnectorKind)),
        deployment_artifacts=[
            "Dockerfile",
            "Makefile",
            "containers/compose.yaml",
            "containers/clickhouse-init.sql",
            "openapi/openapi.json",
        ],
        transport_lanes=[
            "typed FastAPI contract edge",
            "connector-backed parquet and web intake",
            "generated Python and TypeScript client surfaces",
            "compiled Rust signal lane",
            "append-only tracking ledger",
        ],
        store_counts=store_counts,
        notes=[
            (
                "The deployment stack is explicit and versioned, even when the default "
                "runtime remains a single local service edge."
            ),
            (
                "The gateway lane stays narrow: it evaluates packet geometry and "
                "routing posture before downstream orchestration claims more than the "
                "current code can support."
            ),
            (
                "Connector, music, replay, and governance stores remain visible so the "
                "edge route does not become a disconnected glamour layer."
            ),
        ],
    )
