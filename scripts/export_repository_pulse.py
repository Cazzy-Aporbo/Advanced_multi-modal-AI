from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

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
        ("proof/repository-pulse.json", "Exported repository pulse."),
        ("proof/repository-pulse.md", "Readable repository pulse."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        response = client.get("/v1/repository/pulse")
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "repository-pulse.json"
        markdown_path = proof_dir / "repository-pulse.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="repository_pulse_export",
            command="python3 scripts/export_repository_pulse.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Repository pulse export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="repository_pulse_export",
            command="python3 scripts/export_repository_pulse.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Repository pulse regenerated from the live backend."],
        )


def _render_markdown(payload: dict[str, object]) -> str:
    lane_blocks = "\n\n".join(_render_lane_markdown(lane) for lane in payload["lanes"])
    return f"""# Repository Pulse

- Service: `{payload['service']}`
- Version: `{payload['version']}`
- Readiness posture: `{payload['readiness_posture']}`
- Route count: `{payload['route_count']}`
- Test count: `{payload['test_count']}`
- Model count: `{payload['model_count']}`

## Lane status

{lane_blocks}
"""


def _render_lane_markdown(lane: dict[str, object]) -> str:
    files = "\n".join(f"- `{item}`" for item in lane["files"]) or "- none"
    actions = "\n".join(f"- {item}" for item in lane["suggested_actions"]) or "- none"
    artifacts = "\n".join(
        (
            f"- `{item['path']}` · {item['status']} · {item['bytes']} bytes"
            + (
                f" · updated {item['modified_at']}"
                if item.get("modified_at")
                else ""
            )
        )
        for item in lane["artifacts"]
    ) or "- none"
    return f"""### {lane['label']}

- Lane id: `{lane['lane_id']}`
- Emphasis: `{lane['emphasis']}`
- Live score: `{lane['live_score']}`
- Active count: `{lane['active_count']}`
- Warning count: `{lane['warning_count']}`

{lane['summary']}

Files:
{files}

Artifacts:
{artifacts}

Suggested actions:
{actions}
"""


if __name__ == "__main__":
    main()
