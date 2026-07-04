from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import Settings
from .contracts import RepositoryGrowthSnapshot, RuntimeProofBundle, utc_now

REPO_ROOT = Path(__file__).resolve().parents[2]
PROOF_PATH = REPO_ROOT / "proof" / "repository-growth.json"
PUBLIC_SURFACE_FILES = [
    "index.html",
    "advanced-technical-portfolio.html",
    "technical-portfolio.html",
    "model-observatory.html",
    "music-observatory.html",
    "benchmark-observatory.html",
    "cymatic-media-engine.html",
    "industrial-diagnostics.html",
    "industry-profiles.html",
    "field-notes.html",
]
COMMUNITY_FILES = [
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/use_case.yml",
    ".github/pull_request_template.md",
]


def build_repository_growth_snapshot(
    *,
    settings: Settings,
    proof_bundle: RuntimeProofBundle,
    persisted: dict[str, Any] | None = None,
) -> RepositoryGrowthSnapshot:
    payload = persisted or load_persisted_repository_growth()
    existing_community_files = [
        path for path in COMMUNITY_FILES if (REPO_ROOT / path).exists()
    ]
    notes = list(payload.get("notes", []))
    if not payload:
        notes.append(
            "Remote repository metrics appear here after the growth snapshot workflow "
            "records GitHub API and traffic data."
        )
    if len(existing_community_files) < len(COMMUNITY_FILES):
        notes.append(
            "Some contribution and community files are still missing from the repository surface."
        )

    return RepositoryGrowthSnapshot(
        repository=f"{settings.repository_owner}/{settings.repository_name}",
        repository_url=settings.repository_url,
        default_branch=settings.repository_default_branch,
        collection_mode=payload.get("collection_mode", "local_fallback"),
        traffic_window_available=bool(payload.get("traffic_window_available", False)),
        stars=int(payload.get("stars", 0)),
        forks=int(payload.get("forks", 0)),
        watchers=int(payload.get("watchers", 0)),
        subscribers=int(payload.get("subscribers", 0)),
        open_issues=int(payload.get("open_issues", 0)),
        open_pull_requests=int(payload.get("open_pull_requests", 0)),
        contributor_count=int(payload.get("contributor_count", 0)),
        release_count=int(payload.get("release_count", 0)),
        views_14d=int(payload.get("views_14d", 0)),
        unique_visitors_14d=int(payload.get("unique_visitors_14d", 0)),
        clones_14d=int(payload.get("clones_14d", 0)),
        unique_cloners_14d=int(payload.get("unique_cloners_14d", 0)),
        community_health_percent=int(payload.get("community_health_percent", 0)),
        route_count=proof_bundle.route_count,
        test_count=proof_bundle.test_count,
        public_surface_count=sum(
            1 for path in PUBLIC_SURFACE_FILES if (REPO_ROOT / path).exists()
        ),
        proof_export_count=len(list((REPO_ROOT / "proof").glob("*.json")))
        + len(list((REPO_ROOT / "proof").glob("*.md"))),
        docs_count=_count_markdown(REPO_ROOT / "docs") + int((REPO_ROOT / "README.md").exists()),
        example_count=_count_files(REPO_ROOT / "examples"),
        community_file_count=len(existing_community_files),
        notebook_count=len(list(REPO_ROOT.rglob("*.ipynb"))),
        topics=list(payload.get("topics", [])),
        community_files=existing_community_files,
        notes=notes,
        captured_at=payload.get("captured_at", utc_now()),
    )


def load_persisted_repository_growth() -> dict[str, Any]:
    if not PROOF_PATH.exists():
        return {}
    try:
        return json.loads(PROOF_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def render_repository_growth_markdown(snapshot: RepositoryGrowthSnapshot) -> str:
    notes = "\n".join(f"- {item}" for item in snapshot.notes) or "- none"
    topics = ", ".join(snapshot.topics) if snapshot.topics else "none recorded"
    community_files = (
        "\n".join(f"- `{path}`" for path in snapshot.community_files) or "- none"
    )
    return f"""# Repository Growth Snapshot

- Repository: `{snapshot.repository}`
- Captured at: `{snapshot.captured_at}`
- Collection mode: `{snapshot.collection_mode}`
- Traffic window available: `{snapshot.traffic_window_available}`
- Stars: `{snapshot.stars}`
- Forks: `{snapshot.forks}`
- Watchers: `{snapshot.watchers}`
- Subscribers: `{snapshot.subscribers}`
- Open issues: `{snapshot.open_issues}`
- Open pull requests: `{snapshot.open_pull_requests}`
- Contributors: `{snapshot.contributor_count}`
- Releases: `{snapshot.release_count}`
- Views (14d): `{snapshot.views_14d}`
- Unique visitors (14d): `{snapshot.unique_visitors_14d}`
- Clones (14d): `{snapshot.clones_14d}`
- Unique cloners (14d): `{snapshot.unique_cloners_14d}`
- Community health: `{snapshot.community_health_percent}`
- Route count: `{snapshot.route_count}`
- Test count: `{snapshot.test_count}`
- Public surfaces: `{snapshot.public_surface_count}`
- Proof exports: `{snapshot.proof_export_count}`
- Docs count: `{snapshot.docs_count}`
- Example count: `{snapshot.example_count}`
- Community files: `{snapshot.community_file_count}`
- Notebook count: `{snapshot.notebook_count}`
- Topics: {topics}

## Community files

{community_files}

## Notes

{notes}
"""


def _count_markdown(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len(list(directory.rglob("*.md")))


def _count_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len([path for path in directory.rglob("*") if path.is_file()])
