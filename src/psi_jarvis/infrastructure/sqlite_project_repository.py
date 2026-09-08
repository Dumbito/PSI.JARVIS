import sqlite3
from pathlib import Path
from uuid import UUID

from psi_jarvis.domain.project import ReviewProject
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


class SQLiteProjectRepository:
    """Persistencia SQLite de proyectos de revisión científica."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def save(self, project: ReviewProject) -> None:
        import json

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO review_projects (
                    project_id,
                    name,
                    research_question,
                    topic,
                    inclusion_rules,
                    exclusion_rules,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name = excluded.name,
                    research_question = excluded.research_question,
                    topic = excluded.topic,
                    inclusion_rules = excluded.inclusion_rules,
                    exclusion_rules = excluded.exclusion_rules,
                    created_at = excluded.created_at
                """,
                (
                    str(project.project_id),
                    project.name,
                    project.research_question,
                    project.criteria.topic,
                    json.dumps(project.criteria.inclusion),
                    json.dumps(project.criteria.exclusion),
                    project.created_at.isoformat(),
                ),
            )

    def get(self, project_id: UUID) -> ReviewProject | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM review_projects WHERE project_id = ?",
                (str(project_id),),
            ).fetchone()

        if row is None:
            return None

        return self._to_domain(row)

    def list_all(self) -> tuple[ReviewProject, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM review_projects ORDER BY created_at, project_id"
            ).fetchall()

        return tuple(self._to_domain(row) for row in rows)

    @staticmethod
    def _to_domain(row: sqlite3.Row) -> ReviewProject:
        import json
        from datetime import datetime

        from psi_jarvis.domain.criteria.screening import ScreeningCriteria

        criteria = ScreeningCriteria(
            topic=row["topic"],
            inclusion=tuple(json.loads(row["inclusion_rules"])),
            exclusion=tuple(json.loads(row["exclusion_rules"])),
        )

        return ReviewProject(
            project_id=UUID(row["project_id"]),
            name=row["name"],
            research_question=row["research_question"],
            criteria=criteria,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
