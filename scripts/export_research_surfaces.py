from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from advanced_multimodal_ai.api import create_app

    client = TestClient(create_app())
    response = client.get("/v1/research/surfaces")
    response.raise_for_status()
    payload = response.json()

    proof_dir = ROOT / "proof"
    proof_dir.mkdir(parents=True, exist_ok=True)

    json_path = proof_dir / "research-surfaces.json"
    markdown_path = proof_dir / "research-surfaces.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = payload["summary"]
    lane_blocks = "\n\n".join(
        _render_lane_markdown(lane) for lane in payload["lanes"]
    )
    model_blocks = "\n\n".join(
        _render_model_markdown(card) for card in payload["model_cards"]
    )
    finding_blocks = "\n\n".join(
        _render_finding_markdown(finding) for finding in payload["findings"]
    )
    connection_blocks = "\n\n".join(
        _render_connection_markdown(connection)
        for connection in payload["connections"]
    )

    markdown = f"""# Research Surfaces

- Service: `{payload['service']}`
- Version: `{payload['version']}`
- Readiness posture: `{payload['readiness_posture']}`
- Route count: `{summary['route_count']}`
- Test count: `{summary['test_count']}`
- Connector kinds: `{summary['connector_kind_count']}`
- Models: `{summary['model_count']}`
- Runtime-ready models: `{summary['runtime_ready_model_count']}`
- Open questions: `{summary['open_question_count']}`

## Architecture lanes

{lane_blocks}

## Model cards

{model_blocks}

## Findings

{finding_blocks}

## Connections

{connection_blocks}
"""
    markdown_path.write_text(markdown, encoding="utf-8")
    print(json_path)
    print(markdown_path)


def _render_lane_markdown(lane: dict[str, object]) -> str:
    directories = "\n".join(f"- `{item}`" for item in lane["directories"]) or "- none"
    entries = "\n".join(f"- `{item}`" for item in lane["entry_surfaces"]) or "- none"
    outputs = "\n".join(f"- {item}" for item in lane["outputs"]) or "- none"
    proof_points = "\n".join(f"- {item}" for item in lane["proof_points"]) or "- none"
    return f"""### {lane['label']}

- Lane id: `{lane['lane_id']}`
- Layer: `{lane['layer']}`

{lane['purpose']}

Why it exists:
{lane['why_it_exists']}

Directories:
{directories}

Entry surfaces:
{entries}

Outputs:
{outputs}

Proof points:
{proof_points}
"""


def _render_model_markdown(card: dict[str, object]) -> str:
    strengths = "\n".join(f"- {item}" for item in card["strengths"]) or "- none yet"
    limits = "\n".join(f"- {item}" for item in card["limits"]) or "- none named"
    improvements = (
        "\n".join(f"- {item}" for item in card["improvement_paths"]) or "- none named"
    )
    questions = "\n".join(
        (
            f"- **{item['prompt']}**\n"
            f"  - Why it matters: {item['why_it_matters']}\n"
            f"  - Current position: {item['current_position']}"
        )
        for item in card["open_questions"]
    ) or "- none listed"
    surfaces = ", ".join(card["evidence_surfaces"]) or "none"
    files = ", ".join(card["related_files"]) or "none"
    return f"""### {card['label']}

- Model id: `{card['model_id']}`
- Source file: `{card['source_file']}`
- Runtime ready: `{card['runtime_ready']}`
- Supports contract mode: `{card['supports_contract_mode']}`
- Supports research mode: `{card['supports_research_mode']}`
- Evidence surfaces: {surfaces}
- Related files: {files}

{card['role_in_system']}

Why this model lives here:
{card['why_used']}

Strengths:
{strengths}

Limits:
{limits}

Improvement paths:
{improvements}

Open questions:
{questions}
"""


def _render_finding_markdown(finding: dict[str, object]) -> str:
    evidence = "\n".join(f"- {item}" for item in finding["evidence"]) or "- none"
    surfaces = ", ".join(finding["related_surfaces"]) or "none"
    files = ", ".join(finding["related_files"]) or "none"
    return f"""### {finding['title']}

- Lens: `{finding['lens']}`
- Finding id: `{finding['finding_id']}`
- Related surfaces: {surfaces}
- Related files: {files}

{finding['summary']}

Evidence:
{evidence}

Why it matters:
{finding['why_it_matters']}

Next step:
{finding['next_step']}
"""


def _render_connection_markdown(connection: dict[str, object]) -> str:
    files = "\n".join(f"- `{item}`" for item in connection["files"]) or "- none"
    surfaces = "\n".join(f"- `{item}`" for item in connection["api_surfaces"]) or "- none"
    watch_points = (
        "\n".join(f"- {item}" for item in connection["watch_points"]) or "- none"
    )
    return f"""### {connection['title']}

- Connection id: `{connection['connection_id']}`

{connection['summary']}

Files:
{files}

API surfaces:
{surfaces}

Learning value:
{connection['learning_value']}

Watch points:
{watch_points}
"""


if __name__ == "__main__":
    main()
