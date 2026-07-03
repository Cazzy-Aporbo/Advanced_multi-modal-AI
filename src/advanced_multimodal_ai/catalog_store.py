from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import DatasetRecord


class CatalogStore:
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
                CREATE TABLE IF NOT EXISTS dataset_catalog (
                    dataset_id TEXT PRIMARY KEY,
                    dataset_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_dataset(self, record: DatasetRecord) -> DatasetRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO dataset_catalog (
                    dataset_id,
                    dataset_name,
                    version,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.dataset_id,
                    record.dataset_name,
                    record.version,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM dataset_catalog WHERE dataset_id = ?",
                (dataset_id,),
            ).fetchone()
        return (
            DatasetRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def get_latest_by_name(self, dataset_name: str) -> DatasetRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_payload FROM dataset_catalog
                WHERE dataset_name = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (dataset_name,),
            ).fetchone()
        return (
            DatasetRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def get_by_name_version(
        self,
        dataset_name: str,
        version: str,
    ) -> DatasetRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_payload FROM dataset_catalog
                WHERE dataset_name = ? AND version = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (dataset_name, version),
            ).fetchone()
        return (
            DatasetRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_datasets(self, limit: int = 100) -> list[DatasetRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM dataset_catalog
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [DatasetRecord.model_validate(json.loads(row["record_payload"])) for row in rows]

    def count_datasets(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM dataset_catalog").fetchone()
        return int(row["total"]) if row is not None else 0
