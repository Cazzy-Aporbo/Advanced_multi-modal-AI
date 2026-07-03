from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import MusicFeatureWarehouseRun, MusicTrackManifestRecord


class MusicStore:
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
                CREATE TABLE IF NOT EXISTS music_manifests (
                    manifest_id TEXT PRIMARY KEY,
                    track_name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS music_feature_runs (
                    run_id TEXT PRIMARY KEY,
                    manifest_id TEXT NOT NULL,
                    track_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_manifest(self, record: MusicTrackManifestRecord) -> MusicTrackManifestRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO music_manifests (
                    manifest_id,
                    track_name,
                    owner,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.manifest_id,
                    record.track_name,
                    record.owner,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_manifest(self, manifest_id: str) -> MusicTrackManifestRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM music_manifests WHERE manifest_id = ?",
                (manifest_id,),
            ).fetchone()
        return (
            MusicTrackManifestRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_manifests(self, limit: int = 50) -> list[MusicTrackManifestRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM music_manifests
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            MusicTrackManifestRecord.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def save_run(self, record: MusicFeatureWarehouseRun) -> MusicFeatureWarehouseRun:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO music_feature_runs (
                    run_id,
                    manifest_id,
                    track_name,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.manifest_id,
                    record.track_name,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_run(self, run_id: str) -> MusicFeatureWarehouseRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM music_feature_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return (
            MusicFeatureWarehouseRun.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_runs(self, limit: int = 50) -> list[MusicFeatureWarehouseRun]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM music_feature_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            MusicFeatureWarehouseRun.model_validate(json.loads(row["record_payload"]))
            for row in rows
        ]

    def count_manifests(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM music_manifests").fetchone()
        return int(row["total"]) if row is not None else 0

    def count_runs(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM music_feature_runs").fetchone()
        return int(row["total"]) if row is not None else 0

    def total_segments(self) -> int:
        return sum(run.segment_count for run in self.list_runs(limit=1000))
