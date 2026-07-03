from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import DriftBaselineRecord


class DriftStore:
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
                CREATE TABLE IF NOT EXISTS drift_baselines (
                    label TEXT PRIMARY KEY,
                    baseline_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    runtime_mode TEXT NOT NULL,
                    coverage_score REAL NOT NULL,
                    fusion_readiness REAL NOT NULL,
                    modality_profiles TEXT NOT NULL,
                    pairwise_alignment TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_baseline(self, record: DriftBaselineRecord) -> DriftBaselineRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO drift_baselines (
                    label,
                    baseline_id,
                    request_id,
                    model_id,
                    runtime_mode,
                    coverage_score,
                    fusion_readiness,
                    modality_profiles,
                    pairwise_alignment,
                    notes,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(label) DO UPDATE SET
                    baseline_id = excluded.baseline_id,
                    request_id = excluded.request_id,
                    model_id = excluded.model_id,
                    runtime_mode = excluded.runtime_mode,
                    coverage_score = excluded.coverage_score,
                    fusion_readiness = excluded.fusion_readiness,
                    modality_profiles = excluded.modality_profiles,
                    pairwise_alignment = excluded.pairwise_alignment,
                    notes = excluded.notes,
                    created_at = excluded.created_at
                """,
                (
                    record.label,
                    record.baseline_id,
                    record.request_id,
                    record.model_id,
                    record.runtime_mode,
                    record.coverage_score,
                    record.fusion_readiness,
                    json.dumps(
                        [profile.model_dump(mode="json") for profile in record.modality_profiles],
                        sort_keys=True,
                    ),
                    json.dumps(
                        [profile.model_dump(mode="json") for profile in record.pairwise_alignment],
                        sort_keys=True,
                    ),
                    json.dumps(record.notes, sort_keys=True),
                    record.created_at,
                ),
            )
        return record

    def get_baseline(self, label: str) -> DriftBaselineRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM drift_baselines WHERE label = ?",
                (label,),
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def list_baselines(self, limit: int = 50) -> list[DriftBaselineRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM drift_baselines
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def count_baselines(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM drift_baselines").fetchone()
        return int(row["total"]) if row is not None else 0

    def _row_to_record(self, row: sqlite3.Row) -> DriftBaselineRecord:
        return DriftBaselineRecord.model_validate(
            {
                "baseline_id": row["baseline_id"],
                "label": row["label"],
                "request_id": row["request_id"],
                "model_id": row["model_id"],
                "runtime_mode": row["runtime_mode"],
                "coverage_score": row["coverage_score"],
                "fusion_readiness": row["fusion_readiness"],
                "modality_profiles": json.loads(row["modality_profiles"]),
                "pairwise_alignment": json.loads(row["pairwise_alignment"]),
                "notes": json.loads(row["notes"] or "[]"),
                "created_at": row["created_at"],
            }
        )
