from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .config import Settings
from .contracts import ExecutionArtifactState, ExecutionJournalRecord
from .execution_journal_store import ExecutionJournalStore

REPO_ROOT = Path(__file__).resolve().parents[2]


def record_script_execution(
    *,
    lane: str,
    command: str,
    artifacts: list[tuple[str, str]],
    started_at: datetime,
    finished_at: datetime,
    status: str,
    notes: list[str] | None = None,
    settings: Settings | None = None,
) -> ExecutionJournalRecord:
    active_settings = settings or Settings()
    store = ExecutionJournalStore(active_settings.execution_journal_db_path)
    record = ExecutionJournalRecord(
        lane=lane,
        source_kind="script",
        command=command,
        status=status,
        started_at=started_at.astimezone(timezone.utc).isoformat(),
        completed_at=finished_at.astimezone(timezone.utc).isoformat(),
        duration_ms=max((finished_at - started_at).total_seconds() * 1000.0, 0.0),
        notes=notes or [],
        artifacts=[
            _artifact_state(path_text, note=note)
            for path_text, note in artifacts
        ],
    )
    return store.save_record(record)


def script_execution_window() -> tuple[datetime, float]:
    return datetime.now(timezone.utc), perf_counter()


def finish_script_execution(
    *,
    lane: str,
    command: str,
    artifacts: list[tuple[str, str]],
    started_at: datetime,
    start_counter: float,
    status: str,
    notes: list[str] | None = None,
    settings: Settings | None = None,
) -> ExecutionJournalRecord:
    finished_at = datetime.now(timezone.utc)
    duration_ms = max((perf_counter() - start_counter) * 1000.0, 0.0)
    active_settings = settings or Settings()
    store = ExecutionJournalStore(active_settings.execution_journal_db_path)
    record = ExecutionJournalRecord(
        lane=lane,
        source_kind="script",
        command=command,
        status=status,
        started_at=started_at.astimezone(timezone.utc).isoformat(),
        completed_at=finished_at.astimezone(timezone.utc).isoformat(),
        duration_ms=duration_ms,
        notes=notes or [],
        artifacts=[
            _artifact_state(path_text, note=note)
            for path_text, note in artifacts
        ],
    )
    return store.save_record(record)


def _artifact_state(path_text: str, *, note: str) -> ExecutionArtifactState:
    path = REPO_ROOT / path_text
    if not path.exists():
        return ExecutionArtifactState(
            label=path.name,
            path=path_text,
            status="missing",
            note=note,
        )

    stats = path.stat()
    return ExecutionArtifactState(
        label=path.name,
        path=path_text,
        status="present",
        bytes=stats.st_size,
        modified_at=datetime.fromtimestamp(
            stats.st_mtime, tz=timezone.utc
        ).isoformat(),
        note=note,
    )
