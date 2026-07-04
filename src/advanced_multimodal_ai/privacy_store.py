from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import PrivacyRunRecord


class PrivacyStore:
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
                CREATE TABLE IF NOT EXISTS privacy_runs (
                    run_id TEXT PRIMARY KEY,
                    route TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    document_count INTEGER NOT NULL,
                    finding_count INTEGER NOT NULL,
                    risk_score REAL NOT NULL,
                    highest_severity TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_run(self, record: PrivacyRunRecord) -> PrivacyRunRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO privacy_runs (
                    run_id,
                    route,
                    purpose,
                    tenant_id,
                    document_count,
                    finding_count,
                    risk_score,
                    highest_severity,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.route,
                    record.purpose,
                    record.tenant_id,
                    record.document_count,
                    record.finding_count,
                    record.risk_score,
                    record.highest_severity,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_run(self, run_id: str) -> PrivacyRunRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM privacy_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return (
            PrivacyRunRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_runs(self, limit: int = 50) -> list[PrivacyRunRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM privacy_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            PrivacyRunRecord.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def count_runs(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM privacy_runs").fetchone()
        return int(row["total"]) if row is not None else 0
