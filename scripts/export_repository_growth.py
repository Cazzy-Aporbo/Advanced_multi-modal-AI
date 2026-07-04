from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.config import get_settings  # noqa: E402
from advanced_multimodal_ai.contracts import RuntimeProofBundle  # noqa: E402
from advanced_multimodal_ai.execution_journal import (  # noqa: E402
    finish_script_execution,
    script_execution_window,
)
from advanced_multimodal_ai.repository_growth import (  # noqa: E402
    build_repository_growth_snapshot,
    render_repository_growth_markdown,
)

API_ROOT = "https://api.github.com"


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [
        ("proof/repository-growth.json", "Exported repository growth snapshot."),
        ("proof/repository-growth.md", "Readable repository growth snapshot."),
        (
            "proof/repository-growth-history.jsonl",
            "Append-only repository growth history.",
        ),
    ]
    try:
        settings = get_settings()
        persisted = _collect_remote_repository_signals(settings)
        proof_bundle = _load_runtime_proof_bundle()
        snapshot = build_repository_growth_snapshot(
            settings=settings,
            proof_bundle=proof_bundle,
            persisted=persisted,
        )

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "repository-growth.json"
        markdown_path = proof_dir / "repository-growth.md"
        history_path = proof_dir / "repository-growth-history.jsonl"

        json_path.write_text(
            json.dumps(snapshot.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        markdown_path.write_text(
            render_repository_growth_markdown(snapshot),
            encoding="utf-8",
        )
        _append_history(history_path, snapshot.model_dump(mode="json"))

        print(json_path)
        print(markdown_path)
        print(history_path)
    except Exception as exc:
        finish_script_execution(
            lane="repository_growth_export",
            command="python3 scripts/export_repository_growth.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Repository growth export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="repository_growth_export",
            command="python3 scripts/export_repository_growth.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=[
                "Repository growth snapshot regenerated from the live proof bundle "
                "and any GitHub API data available at export time."
            ],
        )


def _load_runtime_proof_bundle() -> RuntimeProofBundle:
    from advanced_multimodal_ai.api import create_app

    client = TestClient(create_app())
    response = client.get("/v1/proof/bundle")
    response.raise_for_status()
    return RuntimeProofBundle.model_validate(response.json())


def _collect_remote_repository_signals(settings) -> dict[str, Any]:
    repository = os.environ.get(
        "GITHUB_REPOSITORY",
        f"{settings.repository_owner}/{settings.repository_name}",
    )
    token = (
        os.environ.get("AMAI_GITHUB_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or ""
    )
    notes: list[str] = []
    payload: dict[str, Any] = {
        "collection_mode": "local_fallback",
        "traffic_window_available": False,
        "topics": [],
        "notes": notes,
    }

    repo_data = _github_get(f"/repos/{repository}", token=token)
    if not repo_data:
        notes.append(
            "GitHub repository metadata was unavailable during this export; "
            "local proof counts remain visible."
        )
        return payload

    payload.update(
        {
            "stars": int(repo_data.get("stargazers_count", 0)),
            "forks": int(repo_data.get("forks_count", 0)),
            "watchers": int(repo_data.get("watchers_count", 0)),
            "subscribers": int(repo_data.get("subscribers_count", 0)),
            "open_issues": int(repo_data.get("open_issues_count", 0)),
            "topics": list(repo_data.get("topics", []) or []),
        }
    )

    contributors = _github_get(f"/repos/{repository}/contributors?per_page=100&anon=1", token=token)
    if isinstance(contributors, list):
        payload["contributor_count"] = len(contributors)
    else:
        notes.append("Contributor count could not be refreshed from the GitHub API.")

    releases = _github_get(f"/repos/{repository}/releases?per_page=100", token=token)
    if isinstance(releases, list):
        payload["release_count"] = len(releases)
    else:
        notes.append("Release count could not be refreshed from the GitHub API.")

    community = _github_get(f"/repos/{repository}/community/profile", token=token)
    if isinstance(community, dict):
        payload["community_health_percent"] = int(community.get("health_percentage", 0))

    pulls = _github_get(
        f"/search/issues?q={quote(f'repo:{repository} is:pr is:open')}",
        token=token,
    )
    if isinstance(pulls, dict):
        payload["open_pull_requests"] = int(pulls.get("total_count", 0))
    else:
        notes.append("Open pull-request count could not be refreshed from the GitHub API.")

    views = _github_get(f"/repos/{repository}/traffic/views", token=token)
    clones = _github_get(f"/repos/{repository}/traffic/clones", token=token)
    if isinstance(views, dict) and isinstance(clones, dict):
        payload.update(
            {
                "traffic_window_available": True,
                "views_14d": int(views.get("count", 0)),
                "unique_visitors_14d": int(views.get("uniques", 0)),
                "clones_14d": int(clones.get("count", 0)),
                "unique_cloners_14d": int(clones.get("uniques", 0)),
            }
        )
        payload["collection_mode"] = "github_api"
    else:
        notes.append(
            "GitHub traffic endpoints were unavailable; stars, forks, and "
            "contributor signals still refreshed."
        )
        payload["collection_mode"] = "github_api_partial"

    payload["captured_at"] = datetime.now(timezone.utc).isoformat()
    return payload


def _github_get(path: str, *, token: str) -> dict[str, Any] | list[Any] | None:
    url = f"{API_ROOT}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "advanced-multimodal-ai-repository-growth",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError):
        return None


def _append_history(path: Path, snapshot: dict[str, Any]) -> None:
    history_row = {
        "captured_at": snapshot["captured_at"],
        "stars": snapshot["stars"],
        "forks": snapshot["forks"],
        "watchers": snapshot["watchers"],
        "open_issues": snapshot["open_issues"],
        "open_pull_requests": snapshot["open_pull_requests"],
        "views_14d": snapshot["views_14d"],
        "clones_14d": snapshot["clones_14d"],
        "route_count": snapshot["route_count"],
        "test_count": snapshot["test_count"],
    }
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                previous = json.loads(lines[-1])
            except json.JSONDecodeError:
                previous = None
            if previous == history_row:
                return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(history_row) + "\n")


if __name__ == "__main__":
    main()
