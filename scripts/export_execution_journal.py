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
        ("proof/execution-journal.json", "Exported execution journal."),
        ("proof/execution-journal.md", "Readable execution journal."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        response = client.get("/v1/execution/journal")
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "execution-journal.json"
        markdown_path = proof_dir / "execution-journal.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="execution_journal_export",
            command="python3 scripts/export_execution_journal.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Execution journal export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="execution_journal_export",
            command="python3 scripts/export_execution_journal.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Execution journal exported from persisted run records."],
        )


def _render_markdown(payload: dict[str, object]) -> str:
    lane_lines = "\n".join(
        f"- `{lane}`: {count}" for lane, count in payload["lane_counts"].items()
    ) or "- none"
    run_blocks = "\n\n".join(
        _render_run_markdown(run) for run in payload["recent_runs"]
    ) or "No runs recorded yet."
    return f"""# Execution Journal

- Total runs: `{payload['total_runs']}`
- Passing runs: `{payload['passing_runs']}`
- Failing runs: `{payload['failing_runs']}`

## Runs by lane

{lane_lines}

## Recent runs

{run_blocks}
"""


def _render_run_markdown(run: dict[str, object]) -> str:
    artifacts = "\n".join(
        f"- `{item['path']}` · {item['status']} · {item['bytes']} bytes"
        for item in run["artifacts"]
    ) or "- none"
    notes = "\n".join(f"- {item}" for item in run["notes"]) or "- none"
    return f"""### {run['lane']} · {run['status']}

- Command: `{run['command']}`
- Duration: `{run['duration_ms']:.2f}ms`
- Started: `{run['started_at']}`
- Completed: `{run['completed_at']}`

Artifacts:
{artifacts}

Notes:
{notes}
"""


if __name__ == "__main__":
    main()
