import sqlite3
from pathlib import Path
from uuid import UUID

from psi_jarvis.domain.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.corpus_repository import CorpusRepository
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


class SQLiteCorpusRepository:
    """Repositorio persistente de corpus bibliográficos mediante SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def save(self, corpus: Corpus) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO corpora (corpus_id, project_id)
                VALUES (?, ?)
                """,
                (str(corpus.corpus_id), str(corpus.project_id)),
            )

            connection.execute(
                "DELETE FROM corpus_papers WHERE corpus_id = ?",
                (str(corpus.corpus_id),),
            )

            for position, paper in enumerate(corpus.papers):
                connection.execute(
                    """
                    INSERT INTO corpus_papers (corpus_id, paper_id, position)
                    VALUES (?, ?, ?)
                    """,
                    (str(corpus.corpus_id), str(paper.id), position),
                )

    def get(self, corpus_id: UUID) -> Corpus | None:
        with self._connect() as connection:
            corpus_row = connection.execute(
                "SELECT corpus_id, project_id FROM corpora WHERE corpus_id = ?",
                (str(corpus_id),),
            ).fetchone()

            if corpus_row is None:
                return None

            paper_rows = connection.execute(
                """
                SELECT p.*
                FROM corpus_papers cp
                JOIN papers p ON p.paper_id = cp.paper_id
                WHERE cp.corpus_id = ?
                ORDER BY cp.position
                """,
                (str(corpus_id),),
            ).fetchall()

        papers = tuple(
            Paper(
                id=UUID(row["paper_id"]),
                title=row["title"],
                authors=tuple(__import__("json").loads(row["authors"] or "[]")),
                abstract=row["abstract"],
                doi=row["doi"],
                pmid=row["pmid"],
                publication_year=row["publication_year"],
                journal=row["journal"],
            )
            for row in paper_rows
        )

        return Corpus(
            corpus_id=UUID(corpus_row["corpus_id"]),
            project_id=UUID(corpus_row["project_id"]),
            papers=papers,
        )

    def list_all(self) -> tuple[Corpus, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT corpus_id FROM corpora ORDER BY rowid"
            ).fetchall()

        corpora = []
        for row in rows:
            corpus = self.get(UUID(row["corpus_id"]))
            if corpus is not None:
                corpora.append(corpus)

        return tuple(corpora)
