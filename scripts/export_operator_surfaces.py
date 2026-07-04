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
        ("proof/operator-surfaces.json", "Exported operator surface bundle."),
        ("proof/operator-surfaces.md", "Readable operator surface bundle."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        app = create_app()
        service = app.state.service
        if service.music_overview(limit=1).feature_run_count == 0:
            service.extract_music_features(service._reference_music_feature_request())

        client = TestClient(app)
        response = client.get("/v1/operators/surfaces")
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "operator-surfaces.json"
        markdown_path = proof_dir / "operator-surfaces.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        command_rows = (
            "\n".join(
                (
                    f"- **{item['label']}** · `{item['method']} {item['route']}` · "
                    f"{item['runtime_lane']} · {item['operator_goal']}"
                )
                for item in payload["commands"]
            )
            or "- no command surfaces yet"
        )
        skill_rows = (
            "\n".join(
                (
                    f"- **{item['label']}** · {item['focus']} · "
                    f"related commands: {', '.join(item['related_commands']) or 'none'}"
                )
                for item in payload["skills"]
            )
            or "- no skill surfaces yet"
        )
        plugin_rows = (
            "\n".join(
                (f"- **{item['label']}** · {item['seam_kind']} · " f"`{item['entrypoint']}`")
                for item in payload["plugins"]
            )
            or "- no plugin surfaces yet"
        )
        speech_rows = (
            "\n".join(
                (
                    f"- **{item['label']}** · {item['focus']} · "
                    f"signals: {', '.join(item['derived_signals'])}"
                )
                for item in payload["speech_tasks"]
            )
            or "- no speech task surfaces yet"
        )
        metric_rows = (
            "\n".join(
                f"- {item['label']}: {item['value']} · {item['note']}"
                for item in payload["metrics"]
            )
            or "- no operator metrics yet"
        )

        markdown = f"""# Operator Surfaces

## Metrics

{metric_rows}

## Command lattice

{command_rows}

## Skill surfaces

{skill_rows}

## Plugin seams

{plugin_rows}

## Speech task lattice

{speech_rows}
"""
        markdown_path.write_text(markdown, encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="operator_surfaces_export",
            command="python3 scripts/export_operator_surfaces.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Operator surface export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="operator_surfaces_export",
            command="python3 scripts/export_operator_surfaces.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=[
                "Operator surfaces regenerated from live runtime proof and music warehouse state."
            ],
        )


if __name__ == "__main__":
    main()
