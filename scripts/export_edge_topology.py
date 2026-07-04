from __future__ import annotations

import json
import sys
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.execution_journal import (  # noqa: E402
    finish_script_execution,
    script_execution_window,
)


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [
        ("proof/edge-topology.json", "Exported edge gateway topology."),
        ("proof/edge-topology.md", "Readable edge gateway topology."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app
        from advanced_multimodal_ai.contracts import EdgePacketRequest, TensorPayload

        app = create_app()
        client = TestClient(app)
        sample_request = EdgePacketRequest(
            jurisdiction="EU_EEA",
            source_region="DE",
            target_region="DE",
            connector_kind="s3_parquet",
            encrypted_in_transit=True,
            modalities={
                "audio": TensorPayload(
                    shape=[1, 8],
                    values=[0.12, 0.18, 0.09, 0.22, 0.15, 0.19, 0.11, 0.17],
                ),
                "text": TensorPayload(
                    shape=[1, 6],
                    values=[0.2, 0.25, 0.15, 0.18, 0.21, 0.19],
                ),
            },
        )
        evaluate_response = client.post(
            "/v1/edge/evaluate",
            json=sample_request.model_dump(mode="json"),
        )
        evaluate_response.raise_for_status()

        topology_response = client.get("/v1/edge/topology")
        topology_response.raise_for_status()
        topology = topology_response.json()

        ledger_response = client.get("/v1/edge/ledger", params={"limit": 6})
        ledger_response.raise_for_status()
        ledger = ledger_response.json()

        payload = {
            "topology": topology,
            "ledger": ledger,
        }

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)
        json_path = proof_dir / "edge-topology.json"
        markdown_path = proof_dir / "edge-topology.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        artifact_rows = "\n".join(
            f"- `{path}`" for path in topology["deployment_artifacts"]
        ) or "- no deployment artifacts recorded"
        transport_rows = "\n".join(
            f"- {lane}" for lane in topology["transport_lanes"]
        ) or "- no transport lanes recorded"
        ledger_rows = "\n".join(
            (
                f"- **{event['route_action']}** · `{event['transaction_id']}` · "
                f"{event['source_region']} → {event['target_region']} · "
                f"entropy {event['overall_entropy_score']:.3f}"
            )
            for event in ledger["recent_events"]
        ) or "- no edge packet events recorded"

        markdown = f"""# Edge Gateway Topology

## Active policy

- jurisdiction: `{topology['active_policy']['jurisdiction']}`
- max entropy limit: `{topology['active_policy']['max_entropy_limit']}`
- max zero ratio: `{topology['active_policy']['max_zero_ratio']}`
- minimum finite ratio: `{topology['active_policy']['min_finite_ratio']}`
- cross-border allowed: `{topology['active_policy']['allow_cross_border']}`
- encryption required: `{topology['active_policy']['require_encryption']}`

## Deployment artifacts

{artifact_rows}

## Transport lanes

{transport_rows}

## Recent ledger events

{ledger_rows}
"""
        markdown_path.write_text(markdown, encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="edge_topology_export",
            command="python3 scripts/export_edge_topology.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Edge topology export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="edge_topology_export",
            command="python3 scripts/export_edge_topology.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=[
                "Edge gateway topology and tracking ledger regenerated from the live runtime."
            ],
        )


if __name__ == "__main__":
    main()
