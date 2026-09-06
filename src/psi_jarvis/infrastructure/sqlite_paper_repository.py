import json
import sqlite3
from pathlib import Path
from uuid import UUID

from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.paper_repository import PaperRepository
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema
from psi_jarvis.infrastructure.sqlite_paper_mapper import paper_from_row


class SQLitePaperRepository:
    """Repositorio persistente de artículos científicos mediante SQLite."""

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

    def save(self, paper: Paper) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO papers (
                    paper_id, title, authors, abstract, doi, pmid,
                    publication_year, journal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(paper_id) DO UPDATE SET
                    title = excluded.title,
                    authors = excluded.authors,
                    abstract = excluded.abstract,
                    doi = excluded.doi,
                    pmid = excluded.pmid,
                    publication_year = excluded.publication_year,
                    journal = excluded.journal
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
            for provenance in paper.provenances:
                receipt = provenance.receipt
                connection.execute(
                    """
                    INSERT INTO acquisition_batches (
                        batch_id, source_key, adapter_key, adapter_version,
                        acquired_at, request_json, request_sha256, input_sha256,
                        source_locator
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(batch_id) DO NOTHING
                    """,
                    (
                        str(receipt.batch_id), receipt.source_key, receipt.adapter_key,
                        receipt.adapter_version, receipt.acquired_at.isoformat(),
                        receipt.request_json, receipt.request_sha256,
                        receipt.input_sha256, receipt.source_locator,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO paper_provenances (
                        provenance_key, paper_id, batch_id, record_ordinal,
                        format_name, format_version, mapping_version,
                        raw_record_sha256, source_record_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(paper_id, batch_id, record_ordinal, raw_record_sha256)
                    DO NOTHING
                    """,
                    (
                        provenance.key, str(paper.id), str(receipt.batch_id),
                        provenance.record_ordinal, provenance.format_name,
                        provenance.format_version, provenance.mapping_version,
                        provenance.raw_record_sha256, provenance.source_record_id,
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

        with self._connect() as connection:
            return paper_from_row(connection, row)

    def list_all(self) -> tuple[Paper, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM papers ORDER BY rowid"
            ).fetchall()

        with self._connect() as connection:
            return tuple(paper_from_row(connection, row) for row in rows)
