from __future__ import annotations

import sys
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.contracts import (  # noqa: E402
    ExecutionJournalSummary,
    ReferenceBenchmarkResult,
    RepositoryPulse,
    ResearchSurfaceBundle,
)
from advanced_multimodal_ai.cymatic_surface import (  # noqa: E402
    build_cymatic_surface_bundle,
)
from advanced_multimodal_ai.execution_journal import (  # noqa: E402
    finish_script_execution,
    script_execution_window,
)


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [
        ("proof/cymatic-surface.json", "Exported cymatic evidence bundle."),
        ("proof/cymatic-surface.md", "Readable cymatic evidence report."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        research = client.get("/v1/research/surfaces")
        research.raise_for_status()
        pulse = client.get("/v1/repository/pulse")
        pulse.raise_for_status()
        benchmark = client.get("/v1/benchmarks/reference")
        benchmark.raise_for_status()
        journal = client.get("/v1/execution/journal")
        journal.raise_for_status()

        bundle = build_cymatic_surface_bundle(
            research_bundle=ResearchSurfaceBundle.model_validate(research.json()),
            repository_pulse=RepositoryPulse.model_validate(pulse.json()),
            benchmark=ReferenceBenchmarkResult.model_validate(benchmark.json()),
            execution_journal=ExecutionJournalSummary.model_validate(journal.json()),
        )

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)
        json_path = proof_dir / "cymatic-surface.json"
        markdown_path = proof_dir / "cymatic-surface.md"

        json_path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")

        band_blocks = "\n".join(
            f"- **{band.label}** · intensity `{band.intensity:.2f}` · drift `{band.drift:.2f}`\n"
            f"  - {band.note}"
            for band in bundle.harmonic_bands
        )
        stage_blocks = "\n\n".join(
            _render_stage_markdown(stage) for stage in bundle.stages
        )
        narrative_blocks = "\n\n".join(
            _render_narrative_markdown(item) for item in bundle.narratives
        )

        markdown = f"""# Cymatic Surface

- Service: `{bundle.service}`
- Version: `{bundle.version}`
- Readiness posture: `{bundle.readiness_posture}`
- Route count: `{bundle.route_count}`
- Tests: `{bundle.test_count}`
- Connector kinds: `{bundle.connector_kind_count}`
- Replay verified: `{bundle.replay_verified}`
- Baseline harmony: `{bundle.baseline_harmony:.2f}`
- Tension index: `{bundle.tension_index:.2f}`
- Active files counted: `{bundle.active_files}`
- Total recorded runs: `{bundle.total_runs}`

## Harmonic bands

{band_blocks}

## Stage cards

{stage_blocks}

## Narrative lanes

{narrative_blocks}

## Continuations

{chr(10).join(f"- `{item}`" for item in bundle.continuation_links)}
"""
        markdown_path.write_text(markdown, encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="cymatic_surface_export",
            command="python3 scripts/export_cymatic_surface.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Cymatic surface export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="cymatic_surface_export",
            command="python3 scripts/export_cymatic_surface.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=[
                (
                    "Cymatic evidence bundle regenerated from benchmark, pulse, "
                    "and research surfaces."
                )
            ],
        )


def _render_stage_markdown(stage: object) -> str:
    metrics = "\n".join(
        f"- **{metric.label}**: `{metric.value}` {metric.unit}".rstrip()
        for metric in stage.metrics
    ) or "- none"
    traces = "\n".join(f"- `{item}`" for item in stage.trace_paths) or "- none"
    files = "\n".join(f"- `{item}`" for item in stage.files) or "- none"
    return f"""### {stage.label}

- Stage id: `{stage.stage_id}`
- Harmony: `{stage.harmony_score:.2f}`
- Friction: `{stage.friction_score:.2f}`

Human read:
{stage.human_read}

Research read:
{stage.research_read}

Business read:
{stage.business_read}

Improvement path:
{stage.improvement_path}

Trace paths:
{traces}

Files:
{files}

Metrics:
{metrics}
"""


def _render_narrative_markdown(item: object) -> str:
    return f"""### {item.title}

- Audience: `{item.audience}`

{item.summary}

Consequence:
{item.consequence}

Continuation:
{item.continuation}
"""


if __name__ == "__main__":
    main()
