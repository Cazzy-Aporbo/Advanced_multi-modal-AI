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
        ("proof/repository-file-map.json", "Exported repository file map."),
        ("proof/repository-file-map.md", "Readable repository file map."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        response = client.get("/v1/repository/file-map")
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "repository-file-map.json"
        markdown_path = proof_dir / "repository-file-map.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="repository_file_map_export",
            command="python3 scripts/export_repository_file_map.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Repository file map export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="repository_file_map_export",
            command="python3 scripts/export_repository_file_map.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Repository file map regenerated from static analysis."],
        )


def _render_markdown(payload: dict[str, object]) -> str:
    lane_lines = "\n".join(
        f"- `{lane}`: `{count}`" for lane, count in payload.get("lane_counts", {}).items()
    )
    language_lines = "\n".join(
        f"- `{language}`: `{count}`"
        for language, count in payload.get("language_counts", {}).items()
    )
    node_blocks = "\n\n".join(
        _render_node_markdown(node) for node in payload.get("top_connected", [])[:12]
    )
    return f"""# Repository File Map

- Service: `{payload['service']}`
- Version: `{payload['version']}`
- Files mapped: `{payload['file_count']}`
- Edges mapped: `{payload['edge_count']}`
- Active Python files: `{payload['active_python_files']}`
- Frontend files: `{payload['frontend_files']}`
- Proof files: `{payload['proof_files']}`

## Lane counts

{lane_lines}

## Language counts

{language_lines}

## Most connected files

{node_blocks}
"""


def _render_node_markdown(node: dict[str, object]) -> str:
    inputs = "\n".join(f"- {item}" for item in node.get("inputs", [])) or "- none"
    outputs = "\n".join(f"- {item}" for item in node.get("outputs", [])) or "- none"
    connects = "\n".join(f"- `{item}`" for item in node.get("connects_to", [])[:8]) or "- none"
    imported_by = "\n".join(f"- `{item}`" for item in node.get("imported_by", [])[:8]) or "- none"
    evidence = "\n".join(f"- {item}" for item in node.get("evidence", [])) or "- none"
    return f"""### `{node['path']}`

- Lane: `{node['lane']}`
- Language: `{node['language']}`
- Status: `{node['status']}`
- Complexity score: `{node['complexity_score']}`
- Lines: `{node['line_count']}`
- Routes: `{node['route_count']}`
- Tests: `{node['test_count']}`

{node['purpose']}

Inputs:
{inputs}

Outputs:
{outputs}

Connects to:
{connects}

Imported by:
{imported_by}

Evidence:
{evidence}
"""


if __name__ == "__main__":
    main()
