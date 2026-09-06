import sqlite3
from datetime import datetime
from uuid import UUID

from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


class SQLiteScreeningRunRepository:
    """Repositorio persistente de ejecuciones de cribado mediante SQLite."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def save(self, run: ScreeningRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO screening_runs (
                    run_id,
                    project_id,
                    criteria_version,
                    started_at,
                    total_input,
                    unique_papers,
                    duplicates_removed,
                    screened_papers
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    criteria_version = excluded.criteria_version,
                    started_at = excluded.started_at,
                    total_input = excluded.total_input,
                    unique_papers = excluded.unique_papers,
                    duplicates_removed = excluded.duplicates_removed,
                    screened_papers = excluded.screened_papers
                """,
                (
                    str(run.run_id),
                    str(run.project_id) if run.project_id is not None else None,
                    run.criteria_version,
                    run.started_at.isoformat(),
                    run.total_input,
                    run.unique_papers,
                    run.duplicates_removed,
                    run.screened_papers,
                ),
            )

    def get(self, run_id: UUID) -> ScreeningRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM screening_runs WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()

        if row is None:
            return None

        return ScreeningRun(
            run_id=UUID(row["run_id"]),
            project_id=UUID(row["project_id"]) if row["project_id"] else None,
            criteria_version=row["criteria_version"],
            started_at=datetime.fromisoformat(row["started_at"]),
            total_input=row["total_input"],
            unique_papers=row["unique_papers"],
            duplicates_removed=row["duplicates_removed"],
            screened_papers=row["screened_papers"],
        )

    def list_all(self) -> tuple[ScreeningRun, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM screening_runs ORDER BY started_at"
            ).fetchall()

        return tuple(
            ScreeningRun(
                run_id=UUID(row["run_id"]),
                project_id=UUID(row["project_id"]) if row["project_id"] else None,
                criteria_version=row["criteria_version"],
                started_at=datetime.fromisoformat(row["started_at"]),
                total_input=row["total_input"],
                unique_papers=row["unique_papers"],
                duplicates_removed=row["duplicates_removed"],
                screened_papers=row["screened_papers"],
            )
            for row in rows
        )
