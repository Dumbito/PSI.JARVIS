from __future__ import annotations

from dataclasses import dataclass
import os
import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

from psi_jarvis.infrastructure.auth import (
    ScopusConnectionManager,
    ScopusOAuthClient,
    default_scopus_token_store,
    load_scopus_environment,
)
from psi_jarvis.infrastructure.connections import build_default_source_connection_registry
from psi_jarvis.infrastructure.sqlite_metadata_history_repository import SQLiteMetadataHistoryRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository


@dataclass(frozen=True)
class DashboardSnapshot:
    projects: int = 0
    papers: int = 0
    screened: int = 0
    pending: int = 0
    included: int = 0
    excluded: int = 0
    conflicts: int = 0
    source_counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class SourceSnapshot:
    key: str
    display_name: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class ScreeningRow:
    paper_id: str
    title: str
    year: int | None
    decision: str
    reason: str
    run_id: str | None
    criteria_version: str | None


@dataclass(frozen=True)
class AuditRow:
    changed_at: str
    paper_id: str
    source_key: str
    source_record_id: str | None
    changed_fields: tuple[str, ...]


def default_database_path() -> Path:
    configured = os.environ.get("PSI_JARVIS_DATABASE_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "psi-jarvis" / "psi.db"


class GuiDataService:
    """Read-only facade over persisted PSI.JARVIS state."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(database_path or default_database_path()).expanduser()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def snapshot(self) -> DashboardSnapshot:
        if not self.database_path.exists():
            return DashboardSnapshot()
        projects = SQLiteProjectRepository(self.database_path).list_all()
        papers = SQLitePaperRepository(self.database_path).list_all()
        included = excluded = 0
        source_counts: dict[str, int] = {}
        with self._connect() as connection:
            try:
                for row in connection.execute("SELECT included, COUNT(*) AS count FROM screening_results GROUP BY included"):
                    if row["included"]:
                        included = int(row["count"])
                    else:
                        excluded = int(row["count"])
            except sqlite3.OperationalError:
                pass
            try:
                for row in connection.execute("SELECT source_key, COUNT(*) AS count FROM acquisition_batches GROUP BY source_key"):
                    source_counts[str(row["source_key"])] = int(row["count"])
            except sqlite3.OperationalError:
                pass
        screened = included + excluded
        return DashboardSnapshot(
            projects=len(projects), papers=len(papers), screened=screened,
            pending=max(0, len(papers) - screened), included=included,
            excluded=excluded, conflicts=0,
            source_counts=tuple(sorted(source_counts.items())),
        )

    def projects(self):
        if not self.database_path.exists():
            return ()
        return SQLiteProjectRepository(self.database_path).list_all()

    def papers(self):
        if not self.database_path.exists():
            return ()
        return SQLitePaperRepository(self.database_path).list_all()

    def screening_rows(self) -> tuple[ScreeningRow, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT sr.paper_id, p.title, p.publication_year, sr.included, sr.reason, sr.run_id, sr.criteria_version "
                    "FROM screening_results sr JOIN papers p ON p.paper_id = sr.paper_id "
                    "ORDER BY p.title COLLATE NOCASE"
                ).fetchall()
        except sqlite3.OperationalError:
            return ()
        return tuple(
            ScreeningRow(
                paper_id=row["paper_id"], title=row["title"], year=row["publication_year"],
                decision="Included" if row["included"] else "Excluded",
                reason=row["reason"], run_id=row["run_id"], criteria_version=row["criteria_version"],
            ) for row in rows
        )

    def audit_rows(self, limit: int = 200) -> tuple[AuditRow, ...]:
        if not self.database_path.exists():
            return ()
        try:
            changes = SQLiteMetadataHistoryRepository(self.database_path).list_all()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(
            AuditRow(
                changed_at=change.changed_at.isoformat(), paper_id=str(change.paper_id),
                source_key=change.source_key, source_record_id=change.source_record_id,
                changed_fields=change.changed_fields,
            ) for change in changes[-limit:]
        )

    def paper_details(self, paper_id: str) -> dict[str, Any] | None:
        if not self.database_path.exists():
            return None
        try:
            paper = SQLitePaperRepository(self.database_path).get(UUID(paper_id))
            if paper is None:
                return None
            with self._connect() as connection:
                provenance_count = connection.execute(
                    "SELECT COUNT(*) FROM paper_provenances WHERE paper_id = ?", (paper_id,)
                ).fetchone()[0]
            return {
                "title": paper.title, "authors": ", ".join(paper.authors),
                "abstract": paper.abstract or "", "doi": paper.doi or "",
                "pmid": paper.pmid or "", "journal": paper.journal or "",
                "year": paper.publication_year or "", "provenance_count": int(provenance_count),
            }
        except (sqlite3.OperationalError, ValueError):
            return None

    def sources(self) -> tuple[SourceSnapshot, ...]:
        try:
            config = load_scopus_environment()
            manager = ScopusConnectionManager(
                config.oauth, default_scopus_token_store(),
                oauth_client=ScopusOAuthClient(config.oauth) if config.oauth is not None else None,
                transport_config=config.transport,
            )
            registry = build_default_source_connection_registry(manager)
            return tuple(
                SourceSnapshot(state.source.key, state.source.display_name, state.status.value, state.detail)
                for state in registry.inspect_all()
            )
        except Exception as exc:
            return (SourceSnapshot("unknown", "Bibliographic sources", "error", str(exc)),)
