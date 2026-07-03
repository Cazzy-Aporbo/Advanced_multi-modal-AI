from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import PipelineRunRecord


class PipelineStore:
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
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id TEXT PRIMARY KEY,
                    stream_id TEXT NOT NULL,
                    batch_label TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_run(self, record: PipelineRunRecord) -> PipelineRunRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO pipeline_runs (
                    run_id,
                    stream_id,
                    batch_label,
                    status,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.stream_id,
                    record.batch_label,
                    record.status,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_run(self, run_id: str) -> PipelineRunRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM pipeline_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return (
            PipelineRunRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_runs(self, limit: int = 50) -> list[PipelineRunRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM pipeline_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            PipelineRunRecord.model_validate(json.loads(row["record_payload"])) for row in rows
        ]

    def count_runs(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM pipeline_runs").fetchone()
        return int(row["total"]) if row is not None else 0
