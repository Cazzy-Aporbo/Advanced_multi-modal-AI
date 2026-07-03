from __future__ import annotations

import json
import sys
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PROOF_DIR = ROOT / "proof"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.execution_journal import (  # noqa: E402
    finish_script_execution,
    script_execution_window,
)


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [
        ("proof/runtime-proof.json", "Exported runtime proof bundle."),
        ("proof/runtime-proof.md", "Readable runtime proof bundle."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        response = client.get("/v1/proof/bundle")
        response.raise_for_status()
        payload = response.json()

        PROOF_DIR.mkdir(exist_ok=True)
        json_path = PROOF_DIR / "runtime-proof.json"
        md_path = PROOF_DIR / "runtime-proof.md"

        json_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        md_path.write_text(_render_markdown(payload), encoding="utf-8")

        print(json_path)
        print(md_path)
    except Exception as exc:
        finish_script_execution(
            lane="proof_export",
            command="python3 scripts/build_runtime_proof_bundle.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Proof export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="proof_export",
            command="python3 scripts/build_runtime_proof_bundle.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Runtime proof bundle regenerated from the live backend."],
        )


def _render_markdown(payload: dict) -> str:
    command_lines = "\n".join(
        f"- `{item['command']}`" for item in payload.get("verification_commands", [])
    )
    artifact_lines = "\n".join(
        f"- `{item['name']}` · {item['status']} · `{item['detail']}`"
        for item in payload.get("verification_artifacts", [])
    )
    connector_lines = "\n".join(
        f"- `{item}`" for item in payload.get("connector_kinds", [])
    )
    return "\n".join(
        [
            "# Runtime Proof Bundle",
            "",
            f"- Service: `{payload['service']}`",
            f"- Version: `{payload['version']}`",
            f"- Environment: `{payload['environment']}`",
            f"- Route count: `{payload['route_count']}`",
            f"- Test count: `{payload['test_count']}`",
            f"- Verification artifacts: `{payload['verification_artifact_count']}`",
            "",
            "## Connector kinds",
            connector_lines or "- none",
            "",
            "## Verification commands",
            command_lines or "- none",
            "",
            "## Verification artifacts",
            artifact_lines or "- none",
            "",
        ]
    )


if __name__ == "__main__":
    main()
