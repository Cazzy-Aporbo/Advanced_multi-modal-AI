from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import OntologySnapshot


class OntologyStore:
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
                CREATE TABLE IF NOT EXISTS ontology_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    snapshot_payload TEXT NOT NULL
                )
                """
            )

    def save_snapshot(self, snapshot: OntologySnapshot) -> OntologySnapshot:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO ontology_snapshots (
                    snapshot_id,
                    tenant_id,
                    label,
                    created_at,
                    snapshot_payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.tenant_id,
                    snapshot.label,
                    snapshot.created_at,
                    json.dumps(snapshot.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> OntologySnapshot | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT snapshot_payload FROM ontology_snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
        return (
            OntologySnapshot.model_validate(json.loads(row["snapshot_payload"]))
            if row is not None
            else None
        )

    def list_snapshots(self, limit: int = 50) -> list[OntologySnapshot]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT snapshot_payload FROM ontology_snapshots
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            OntologySnapshot.model_validate(json.loads(row["snapshot_payload"]))
            for row in rows
        ]

    def count_snapshots(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM ontology_snapshots").fetchone()
        return int(row["total"]) if row is not None else 0
