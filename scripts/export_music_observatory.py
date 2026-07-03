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
        ("proof/music-observatory.json", "Exported music observatory bundle."),
        ("proof/music-observatory.md", "Readable music observatory report."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        app = create_app()
        service = app.state.service
        if service.music_overview(limit=1).feature_run_count == 0:
            service.extract_music_features(service._reference_music_feature_request())

        client = TestClient(app)
        response = client.get("/v1/music/snapshot")
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "music-observatory.json"
        markdown_path = proof_dir / "music-observatory.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        overview = payload["overview"]
        drift = payload["drift"]
        change_proof = payload["change_proof"]
        segment_slice = payload["segment_slice"]
        alignment_preview = payload["alignment_preview"]

        manifest_rows = "\n".join(
            (
                f"- `{item['track_name']}` · {item['source_kind']} · "
                f"{', '.join(item['genres']) or 'unlabeled'}"
            )
            for item in overview["recent_manifests"]
        ) or "- no manifest records yet"
        run_rows = "\n".join(
            (
                f"- `{item['track_name']}` · {item['segment_count']} segments · "
                f"entropy {item['benchmark']['average_entropy_score']:.3f} · "
                f"tempo {item['benchmark']['average_tempo_proxy_bpm']:.1f} bpm"
            )
            for item in overview["recent_runs"]
        ) or "- no feature runs yet"
        top_genres = "\n".join(
            f"- {genre}: {count}"
            for genre, count in overview["genre_counts"].items()
        ) or "- none yet"
        findings = "\n".join(f"- {item}" for item in overview["top_findings"]) or "- none yet"
        drift_rows = "\n".join(
            (
                f"- **{item['label']}** · {item['status']} · "
                f"score {item['score']:.2f} · {item['evidence']}"
            )
            for item in drift["indicators"]
        ) or "- none yet"
        change_rows = "\n".join(
            f"- **{item['title']}** · {item['summary']}"
            for item in change_proof["changes"]
        ) or "- none yet"
        segment_rows = "\n".join(
            (
                f"- `{item['track_name']}` · {item['label']} · "
                f"{item['start_ms']}–{item['end_ms']} ms · "
                f"speaker {item.get('speaker') or 'unlabeled'} · "
                f"entropy {item.get('entropy_score', 0.0):.3f} · "
                f"repetition {item.get('repetition_ratio', 0.0):.3f}"
            )
            for item in segment_slice["rows"][:8]
        ) or "- none yet"

        markdown = f"""# Music Observatory

- Manifest count: `{overview['manifest_count']}`
- Feature runs: `{overview['feature_run_count']}`
- Total segments: `{overview['total_segments']}`

## Top findings

{findings}

## Drift watch

{drift_rows}

## Change proof

{change_rows}

## Recent manifests

{manifest_rows}

## Recent feature runs

{run_rows}

## Genre coverage

{top_genres}

## Segment slice

{segment_rows}

## Alignment preview

- Windows: `{len(alignment_preview['windows'])}`
- Uncovered modalities: `{', '.join(alignment_preview['uncovered_modalities']) or 'none'}`
"""
        markdown_path.write_text(markdown, encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="music_observatory_export",
            command="python3 scripts/export_music_observatory.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Music observatory export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="music_observatory_export",
            command="python3 scripts/export_music_observatory.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Music observatory regenerated from the persisted warehouse lane."],
        )


if __name__ == "__main__":
    main()
