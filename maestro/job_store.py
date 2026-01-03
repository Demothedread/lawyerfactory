import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


JOB_STORE_STAGE_ORDER = ("ocr", "shotlist", "research", "drafting", "review")


class JobStore:
    """SQLite-backed store for maestro pipeline jobs."""

    def __init__(self, job_store_path: str = "maestro_jobs.sqlite3") -> None:
        self._job_store_path = job_store_path
        self._job_store_initialize()

    def _job_store_connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._job_store_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _job_store_initialize(self) -> None:
        with self._job_store_connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    current_stage TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_stages (
                    job_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output_json TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (job_id, stage)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_sections (
                    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    section_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def job_store_create_job(
        self, documents: list[dict[str, Any]], metadata: dict[str, Any]
    ) -> str:
        job_id = str(uuid.uuid4())
        created_at = self._job_store_now()
        payload = {"documents": documents, **metadata}
        with self._job_store_connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id,
                    status,
                    current_stage,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    "pending",
                    None,
                    json.dumps(payload),
                    created_at,
                    created_at,
                ),
            )
            for stage in JOB_STORE_STAGE_ORDER:
                connection.execute(
                    """
                    INSERT INTO job_stages (job_id, stage, status, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (job_id, stage, "pending", created_at),
                )
        return job_id

    def job_store_update_job(
        self, job_id: str, status: str, current_stage: str | None
    ) -> None:
        updated_at = self._job_store_now()
        with self._job_store_connect() as connection:
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, current_stage = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (status, current_stage, updated_at, job_id),
            )

    def job_store_update_stage(
        self,
        job_id: str,
        stage: str,
        status: str,
        output: dict[str, Any] | None,
    ) -> None:
        updated_at = self._job_store_now()
        with self._job_store_connect() as connection:
            row = connection.execute(
                """
                SELECT started_at, completed_at
                FROM job_stages
                WHERE job_id = ? AND stage = ?
                """,
                (job_id, stage),
            ).fetchone()
            started_at = row["started_at"] if row else None
            completed_at = row["completed_at"] if row else None
            if status == "in_progress" and not started_at:
                started_at = updated_at
            if status == "completed":
                completed_at = updated_at
            connection.execute(
                """
                UPDATE job_stages
                SET status = ?,
                    output_json = ?,
                    started_at = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE job_id = ? AND stage = ?
                """,
                (
                    status,
                    json.dumps(output) if output is not None else None,
                    started_at,
                    completed_at,
                    updated_at,
                    job_id,
                    stage,
                ),
            )
        job_status = (
            "in_progress" if status in {"in_progress", "completed"} else status
        )
        self.job_store_update_job(job_id, job_status, stage)

    def job_store_add_section(
        self, job_id: str, section_key: str, title: str, content: str
    ) -> None:
        created_at = self._job_store_now()
        with self._job_store_connect() as connection:
            connection.execute(
                """
                INSERT INTO job_sections (
                    job_id,
                    section_key,
                    title,
                    content,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, section_key, title, content, created_at),
            )

    def job_store_get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._job_store_connect() as connection:
            job_row = connection.execute(
                """
                SELECT job_id,
                       status,
                       current_stage,
                       metadata_json,
                       created_at,
                       updated_at
                FROM jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            if not job_row:
                return None
            stage_rows = connection.execute(
                """
                SELECT stage,
                       status,
                       output_json,
                       started_at,
                       completed_at,
                       updated_at
                FROM job_stages
                WHERE job_id = ?
                ORDER BY stage
                """,
                (job_id,),
            ).fetchall()
        metadata = json.loads(job_row["metadata_json"])
        stage_map = {
            row["stage"]: {
                "stage": row["stage"],
                "status": row["status"],
                "output": (
                    json.loads(row["output_json"]) if row["output_json"] else None
                ),
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "updated_at": row["updated_at"],
            }
            for row in stage_rows
        }
        stages = [
            stage_map[stage]
            for stage in JOB_STORE_STAGE_ORDER
            if stage in stage_map
        ]
        return {
            "job_id": job_row["job_id"],
            "status": job_row["status"],
            "current_stage": job_row["current_stage"],
            "metadata": metadata,
            "created_at": job_row["created_at"],
            "updated_at": job_row["updated_at"],
            "stages": stages,
        }

    def job_store_list_sections(self, job_id: str) -> list[dict[str, Any]]:
        with self._job_store_connect() as connection:
            section_rows = connection.execute(
                """
                SELECT section_key, title, content, created_at
                FROM job_sections
                WHERE job_id = ?
                ORDER BY section_id
                """,
                (job_id,),
            ).fetchall()
        return [
            {
                "section_key": row["section_key"],
                "title": row["title"],
                "content": row["content"],
                "created_at": row["created_at"],
            }
            for row in section_rows
        ]

    def job_store_stage_output(self, job_id: str, stage: str) -> dict[str, Any] | None:
        with self._job_store_connect() as connection:
            stage_row = connection.execute(
                """
                SELECT output_json
                FROM job_stages
                WHERE job_id = ? AND stage = ?
                """,
                (job_id, stage),
            ).fetchone()
        if not stage_row or not stage_row["output_json"]:
            return None
        return json.loads(stage_row["output_json"])

    @staticmethod
    def _job_store_now() -> str:
        return datetime.now(timezone.utc).isoformat()
