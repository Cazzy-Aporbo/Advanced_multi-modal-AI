from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import ConnectorRunRecord, WebFetchReceipt


class ConnectorStore:
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
                CREATE TABLE IF NOT EXISTS connector_runs (
                    run_id TEXT PRIMARY KEY,
                    dataset_name TEXT NOT NULL,
                    connector_kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_run(self, record: ConnectorRunRecord) -> ConnectorRunRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO connector_runs (
                    run_id,
                    dataset_name,
                    connector_kind,
                    source,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.dataset_name,
                    record.connector_kind,
                    record.source,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_run(self, run_id: str) -> ConnectorRunRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM connector_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return (
            ConnectorRunRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_runs(self, limit: int = 50) -> list[ConnectorRunRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM connector_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ConnectorRunRecord.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def get_latest_web_receipt(self, domain: str, limit: int = 200) -> WebFetchReceipt | None:
        normalized = domain.strip().lower()
        if normalized.startswith("www."):
            normalized = normalized[4:]
        for record in self.list_runs(limit=limit):
            receipt = record.web_receipt
            if receipt is None:
                continue
            receipt_domain = receipt.domain.strip().lower()
            if receipt_domain.startswith("www."):
                receipt_domain = receipt_domain[4:]
            if receipt_domain == normalized:
                return receipt
        return None

    def count_runs(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM connector_runs").fetchone()
        return int(row["total"]) if row is not None else 0
