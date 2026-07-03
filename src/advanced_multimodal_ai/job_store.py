from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from uuid import uuid4

from .contracts import AsyncJobRecord, AsyncJobSubmissionResponse, JobStatus, utc_now


class JobStore:
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
                CREATE TABLE IF NOT EXISTS async_jobs (
                    job_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    started_at TEXT NOT NULL DEFAULT '',
                    completed_at TEXT NOT NULL DEFAULT '',
                    record_count INTEGER NOT NULL,
                    request_payload TEXT NOT NULL,
                    result_payload TEXT NOT NULL DEFAULT '{}',
                    error_message TEXT NOT NULL DEFAULT ''
                )
                """
            )

    def create_job(
        self,
        kind: str,
        request_payload: dict,
        record_count: int,
    ) -> AsyncJobSubmissionResponse:
        submission = AsyncJobSubmissionResponse(
            job_id=str(uuid4()),
            kind=kind,
            status="queued",
            record_count=record_count,
        )
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO async_jobs (
                    job_id, kind, status, submitted_at, record_count, request_payload
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    submission.job_id,
                    kind,
                    submission.status,
                    submission.submitted_at,
                    record_count,
                    json.dumps(request_payload, sort_keys=True),
                ),
            )
        return submission

    def mark_running(self, job_id: str) -> None:
        self._update_state(job_id=job_id, status="running", started_at=utc_now())

    def mark_completed(self, job_id: str, result_payload: dict) -> None:
        self._update_state(
            job_id=job_id,
            status="completed",
            completed_at=utc_now(),
            result_payload=json.dumps(result_payload, sort_keys=True),
            error_message="",
        )

    def mark_failed(self, job_id: str, error_message: str) -> None:
        self._update_state(
            job_id=job_id,
            status="failed",
            completed_at=utc_now(),
            error_message=error_message,
        )

    def _update_state(
        self,
        job_id: str,
        status: JobStatus,
        started_at: str | None = None,
        completed_at: str | None = None,
        result_payload: str | None = None,
        error_message: str | None = None,
    ) -> None:
        fields = ["status = ?"]
        values: list[object] = [status]
        if started_at is not None:
            fields.append("started_at = ?")
            values.append(started_at)
        if completed_at is not None:
            fields.append("completed_at = ?")
            values.append(completed_at)
        if result_payload is not None:
            fields.append("result_payload = ?")
            values.append(result_payload)
        if error_message is not None:
            fields.append("error_message = ?")
            values.append(error_message)
        values.append(job_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                f"UPDATE async_jobs SET {', '.join(fields)} WHERE job_id = ?",
                values,
            )

    def get_job(self, job_id: str) -> AsyncJobRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM async_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def list_jobs(self, limit: int = 20) -> list[AsyncJobRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM async_jobs
                ORDER BY submitted_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def count_jobs(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM async_jobs").fetchone()
        return int(row["total"]) if row is not None else 0

    def _row_to_record(self, row: sqlite3.Row) -> AsyncJobRecord:
        return AsyncJobRecord(
            job_id=row["job_id"],
            kind=row["kind"],
            status=row["status"],
            submitted_at=row["submitted_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            record_count=row["record_count"],
            request_payload=json.loads(row["request_payload"]),
            result_payload=json.loads(row["result_payload"] or "{}"),
            error_message=row["error_message"],
        )
