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
        ("proof/readiness-report.json", "Exported readiness report."),
        ("proof/readiness-report.md", "Readable readiness report."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        response = client.get("/v1/readiness/report")
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "readiness-report.json"
        markdown_path = proof_dir / "readiness-report.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        checks = "\n".join(
            f"- `{item['state']}` {item['name']}: {item['detail']}"
            for item in payload["checks"]
        )
        blockers = "\n".join(f"- {item}" for item in payload["blockers"]) or "- none"
        boundaries = "\n".join(
            f"- **{item['area']}**: {item['detail']}"
            for item in payload["boundaries"]
        )
        markdown = f"""# Runtime Readiness Report

- Posture: `{payload['posture']}`
- Route count: `{payload['route_count']}`
- Test count: `{payload['test_count']}`
- Connector kinds: `{', '.join(payload['connector_kinds'])}`
- Compiled recipes: `{payload['compiled_recipe_count']}`
- Fully resolved recipes: `{payload['resolved_recipe_count']}`

## Checks

{checks}

## Blockers

{blockers}

## Boundaries

{boundaries}
"""
        markdown_path.write_text(markdown, encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="readiness_export",
            command="python3 scripts/export_readiness_report.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Readiness export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="readiness_export",
            command="python3 scripts/export_readiness_report.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Readiness report regenerated from the live backend."],
        )


if __name__ == "__main__":
    main()
