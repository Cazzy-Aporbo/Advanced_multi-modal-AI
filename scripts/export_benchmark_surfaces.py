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
        ("proof/benchmark-surfaces.json", "Exported reference benchmark surface."),
        ("proof/benchmark-surfaces.md", "Readable reference benchmark surface."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        response = client.post(
            "/v1/benchmarks/reference",
            json={
                "label": "public-reference-lane",
                "model_id": "adaptive_transformer",
                "batch_size": 4,
                "max_workers": 4,
                "include_connector_ingest": True,
                "include_batch_job": True,
                "include_smoke_benchmark": True,
            },
        )
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "benchmark-surfaces.json"
        markdown_path = proof_dir / "benchmark-surfaces.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        markdown_path.write_text(_render_markdown(payload), encoding="utf-8")

        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="benchmark_surface_export",
            command="python3 scripts/export_benchmark_surfaces.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Benchmark surface export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="benchmark_surface_export",
            command="python3 scripts/export_benchmark_surfaces.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Reference benchmark surface regenerated from the live backend."],
        )


def _render_markdown(payload: dict[str, object]) -> str:
    stage_lines: list[str] = []
    for stage in payload.get("stages", []):
        notes = "\n".join(f"  - {note}" for note in stage.get("notes", [])) or "  - none"
        artifacts = ", ".join(stage.get("artifacts", [])) or "none"
        stage_lines.append(
            "\n".join(
                [
                    f"### {stage['label']}",
                    f"- Stage id: `{stage['stage_id']}`",
                    f"- Status: `{stage['status']}`",
                    f"- Duration: `{stage['duration_ms']:.2f}` ms",
                    f"- Record count: `{stage['record_count']}`",
                    f"- Artifacts: {artifacts}",
                    "Notes:",
                    notes,
                ]
            )
        )

    notes = "\n".join(f"- {item}" for item in payload.get("notes", [])) or "- none"

    return f"""# Reference Benchmark Surface

- Benchmark id: `{payload['benchmark_id']}`
- Label: `{payload['label']}`
- Model id: `{payload['model_id']}`
- Route count: `{payload['route_count']}`
- Verification artifacts: `{payload['verification_artifact_count']}`
- Stage count: `{payload['stage_count']}`
- Row count: `{payload['row_count']}`
- Pipeline run id: `{payload.get('pipeline_run_id', '') or 'n/a'}`
- Replay frames: `{payload.get('replay_frame_count', 0)}`
- Replay verified: `{payload.get('replay_verified', False)}`
- Total duration: `{payload['total_duration_ms']:.2f}` ms

## Notes

{notes}

## Stages

{'\n\n'.join(stage_lines)}
"""


if __name__ == "__main__":
    main()
