from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import (
    ChangeControlRecord,
    DataLifecyclePolicyRecord,
    SupplyChainSnapshotRecord,
)


class StewardshipStore:
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
                CREATE TABLE IF NOT EXISTS lifecycle_policies (
                    policy_id TEXT PRIMARY KEY,
                    dataset_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS change_controls (
                    change_id TEXT PRIMARY KEY,
                    change_kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS supply_chain_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_lifecycle_policy(
        self, record: DataLifecyclePolicyRecord
    ) -> DataLifecyclePolicyRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO lifecycle_policies (
                    policy_id,
                    dataset_name,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    record.policy_id,
                    record.dataset_name,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_lifecycle_policy(self, policy_id: str) -> DataLifecyclePolicyRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM lifecycle_policies WHERE policy_id = ?",
                (policy_id,),
            ).fetchone()
        return (
            DataLifecyclePolicyRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def get_latest_lifecycle_for_dataset(
        self, dataset_name: str
    ) -> DataLifecyclePolicyRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_payload FROM lifecycle_policies
                WHERE dataset_name = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (dataset_name,),
            ).fetchone()
        return (
            DataLifecyclePolicyRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_lifecycle_policies(self, limit: int = 100) -> list[DataLifecyclePolicyRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM lifecycle_policies
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            DataLifecyclePolicyRecord.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def save_change_control(self, record: ChangeControlRecord) -> ChangeControlRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO change_controls (
                    change_id,
                    change_kind,
                    status,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.change_id,
                    record.change_kind,
                    record.status,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_change_control(self, change_id: str) -> ChangeControlRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM change_controls WHERE change_id = ?",
                (change_id,),
            ).fetchone()
        return (
            ChangeControlRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_change_controls(self, limit: int = 100) -> list[ChangeControlRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM change_controls
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ChangeControlRecord.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def save_supply_chain_snapshot(
        self, record: SupplyChainSnapshotRecord
    ) -> SupplyChainSnapshotRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO supply_chain_snapshots (
                    snapshot_id,
                    label,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    record.snapshot_id,
                    record.label,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_supply_chain_snapshot(self, snapshot_id: str) -> SupplyChainSnapshotRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM supply_chain_snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
        return (
            SupplyChainSnapshotRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_supply_chain_snapshots(
        self, limit: int = 100
    ) -> list[SupplyChainSnapshotRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM supply_chain_snapshots
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            SupplyChainSnapshotRecord.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def count_lifecycle_policies(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM lifecycle_policies"
            ).fetchone()
        return int(row["total"]) if row is not None else 0

    def count_change_controls(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM change_controls"
            ).fetchone()
        return int(row["total"]) if row is not None else 0

    def count_supply_chain_snapshots(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM supply_chain_snapshots"
            ).fetchone()
        return int(row["total"]) if row is not None else 0
