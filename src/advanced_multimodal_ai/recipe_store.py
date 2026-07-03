from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .contracts import RecipeRecord


class RecipeStore:
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
                CREATE TABLE IF NOT EXISTS compiled_recipes (
                    recipe_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_payload TEXT NOT NULL
                )
                """
            )

    def save_recipe(self, record: RecipeRecord) -> RecipeRecord:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO compiled_recipes (
                    recipe_id,
                    label,
                    objective,
                    created_at,
                    record_payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.recipe_id,
                    record.label,
                    record.objective,
                    record.created_at,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                ),
            )
        return record

    def get_recipe(self, recipe_id: str) -> RecipeRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_payload FROM compiled_recipes WHERE recipe_id = ?",
                (recipe_id,),
            ).fetchone()
        return (
            RecipeRecord.model_validate(json.loads(row["record_payload"]))
            if row is not None
            else None
        )

    def list_recipes(self, limit: int = 100) -> list[RecipeRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_payload FROM compiled_recipes
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [RecipeRecord.model_validate(json.loads(row["record_payload"])) for row in rows]

    def count_recipes(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM compiled_recipes").fetchone()
        return int(row["total"]) if row is not None else 0

