import json
import sqlite3
from pathlib import Path
from uuid import UUID

from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.paper_repository import PaperRepository
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


class SQLitePaperRepository:
    """Repositorio persistente de artículos científicos mediante SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def save(self, paper: Paper) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO papers (
                    paper_id, title, authors, abstract, doi, pmid,
                    publication_year, journal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(paper.id),
                    paper.title,
                    json.dumps(paper.authors),
                    paper.abstract,
                    paper.doi,
                    paper.pmid,
                    paper.publication_year,
                    paper.journal,
                ),
            )

    def get(self, paper_id: UUID) -> Paper | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM papers WHERE paper_id = ?",
                (str(paper_id),),
            ).fetchone()

        if row is None:
            return None

        return self._from_row(row)

    def list_all(self) -> tuple[Paper, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM papers ORDER BY rowid"
            ).fetchall()

        return tuple(self._from_row(row) for row in rows)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Paper:
        return Paper(
            id=UUID(row["paper_id"]),
            title=row["title"],
            authors=tuple(json.loads(row["authors"] or "[]")),
            abstract=row["abstract"],
            doi=row["doi"],
            pmid=row["pmid"],
            publication_year=row["publication_year"],
            journal=row["journal"],
        )
