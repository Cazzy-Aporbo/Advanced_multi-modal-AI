from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import ExecutionJournalRecord, ExecutionJournalSummary


class ExecutionJournalStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_journal (
                    journal_id TEXT PRIMARY KEY,
                    lane TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    notes_json TEXT NOT NULL,
                    artifacts_json TEXT NOT NULL
                )
                """
            )

    def save_record(self, record: ExecutionJournalRecord) -> ExecutionJournalRecord:
        payload = record.model_dump(mode="json")
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO execution_journal (
                    journal_id,
                    lane,
                    source_kind,
                    command,
                    status,
                    started_at,
                    completed_at,
                    duration_ms,
                    notes_json,
                    artifacts_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.journal_id,
                    record.lane,
                    record.source_kind,
                    record.command,
                    record.status,
                    record.started_at,
                    record.completed_at,
                    record.duration_ms,
                    json.dumps(payload["notes"], sort_keys=True),
                    json.dumps(payload["artifacts"], sort_keys=True),
                ),
            )
        return record

    def list_records(self, limit: int = 20) -> list[ExecutionJournalRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM execution_journal
                ORDER BY completed_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def count_records(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM execution_journal"
            ).fetchone()
        return int(row["total"]) if row is not None else 0

    def count_by_lane(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT lane, COUNT(*) AS total
                FROM execution_journal
                GROUP BY lane
                ORDER BY total DESC, lane ASC
                """
            ).fetchall()
        return {str(row["lane"]): int(row["total"]) for row in rows}

    def build_summary(self, limit: int = 20) -> ExecutionJournalSummary:
        recent_runs = self.list_records(limit=limit)
        total_runs = self.count_records()
        status_counts = self.count_by_status()
        return ExecutionJournalSummary(
            total_runs=total_runs,
            passing_runs=status_counts.get("pass", 0),
            failing_runs=status_counts.get("fail", 0),
            lane_counts=self.count_by_lane(),
            recent_runs=recent_runs,
        )

    def count_by_status(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT status, COUNT(*) AS total
                FROM execution_journal
                GROUP BY status
                ORDER BY total DESC, status ASC
                """
            ).fetchall()
        return {str(row["status"]): int(row["total"]) for row in rows}

    def _row_to_record(self, row: sqlite3.Row) -> ExecutionJournalRecord:
        return ExecutionJournalRecord(
            journal_id=row["journal_id"],
            lane=row["lane"],
            source_kind=row["source_kind"],
            command=row["command"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            duration_ms=float(row["duration_ms"]),
            notes=json.loads(row["notes_json"]),
            artifacts=json.loads(row["artifacts_json"]),
        )
