from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import EdgeTrackingLedgerEntry, EdgeTrackingLedgerSummary


class TrackingLedgerStore:
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
                CREATE TABLE IF NOT EXISTS edge_tracking_ledger (
                    event_id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    jurisdiction TEXT NOT NULL,
                    source_region TEXT NOT NULL,
                    target_region TEXT NOT NULL,
                    route_action TEXT NOT NULL,
                    manifest_hash TEXT NOT NULL,
                    overall_entropy_score REAL NOT NULL,
                    highest_modality_risk REAL NOT NULL,
                    encrypted_in_transit INTEGER NOT NULL,
                    cross_border INTEGER NOT NULL,
                    connector_kind TEXT NOT NULL,
                    ledger_parent_hash TEXT NOT NULL,
                    ledger_hash TEXT NOT NULL,
                    notes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_entry(self, entry: EdgeTrackingLedgerEntry) -> EdgeTrackingLedgerEntry:
        payload = entry.model_dump(mode="json")
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO edge_tracking_ledger (
                    event_id,
                    transaction_id,
                    jurisdiction,
                    source_region,
                    target_region,
                    route_action,
                    manifest_hash,
                    overall_entropy_score,
                    highest_modality_risk,
                    encrypted_in_transit,
                    cross_border,
                    connector_kind,
                    ledger_parent_hash,
                    ledger_hash,
                    notes_json,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.event_id,
                    entry.transaction_id,
                    entry.jurisdiction,
                    entry.source_region,
                    entry.target_region,
                    entry.route_action,
                    entry.manifest_hash,
                    entry.overall_entropy_score,
                    entry.highest_modality_risk,
                    1 if entry.encrypted_in_transit else 0,
                    1 if entry.cross_border else 0,
                    entry.connector_kind,
                    entry.ledger_parent_hash,
                    entry.ledger_hash,
                    json.dumps(entry.notes, sort_keys=True),
                    entry.created_at,
                    json.dumps(payload, sort_keys=True),
                ),
            )
        return entry

    def list_entries(self, limit: int = 20) -> list[EdgeTrackingLedgerEntry]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM edge_tracking_ledger
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            EdgeTrackingLedgerEntry.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def count_entries(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM edge_tracking_ledger"
            ).fetchone()
        return int(row["total"]) if row is not None else 0

    def latest_hash(self) -> str:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT ledger_hash FROM edge_tracking_ledger
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
        return str(row["ledger_hash"]) if row is not None else ""

    def count_by_action(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT route_action, COUNT(*) AS total
                FROM edge_tracking_ledger
                GROUP BY route_action
                ORDER BY total DESC, route_action ASC
                """
            ).fetchall()
        return {str(row["route_action"]): int(row["total"]) for row in rows}

    def build_summary(self, limit: int = 20) -> EdgeTrackingLedgerSummary:
        return EdgeTrackingLedgerSummary(
            total_events=self.count_entries(),
            action_counts=self.count_by_action(),
            recent_events=self.list_entries(limit=limit),
        )
