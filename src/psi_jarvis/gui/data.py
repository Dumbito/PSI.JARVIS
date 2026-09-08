from __future__ import annotations

from dataclasses import dataclass
import os
import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

from psi_jarvis.domain.analysis.author_analysis import AuthorAnalysis
from psi_jarvis.domain.analysis.deduplication_analysis import DeduplicationAnalysis
from psi_jarvis.domain.analysis.exclusion_reason_analysis import ExclusionReasonAnalysis
from psi_jarvis.domain.analysis.journal_analysis import JournalAnalysis
from psi_jarvis.domain.analysis.publication_year_analysis import PublicationYearAnalysis
from psi_jarvis.domain.analysis.rule_analysis import RuleAnalysis
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
from psi_jarvis.infrastructure.sqlite_screening_audit_repository import SQLiteScreeningAuditRepository
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository


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

@dataclass(frozen=True)
class ScreeningRunSnapshot:
    run_id: str
    project_id: str | None
    criteria_version: str
    started_at: str
    total_input: int
    unique_papers: int
    duplicates_removed: int
    screened_papers: int

@dataclass(frozen=True)
class MetadataQualitySnapshot:
    total_papers: int = 0
    with_abstract: int = 0
    with_authors: int = 0
    with_doi: int = 0
    with_pmid: int = 0
    with_journal: int = 0
    with_year: int = 0

@dataclass(frozen=True)
class ProjectSnapshot:
    project_id: str
    name: str
    research_question: str
    topic: str
    inclusion: tuple[str, ...]
    exclusion: tuple[str, ...]
    created_at: str
    screening_runs: int
    screened_papers: int

@dataclass(frozen=True)
class ScreeningDetail:
    paper_id: str
    title: str
    decision: str
    reason: str
    run_id: str | None
    criteria_version: str | None
    matched_rules: tuple[str, ...] = ()
    failed_rules: tuple[str, ...] = ()
    audit_id: str | None = None


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
        try:
            projects = SQLiteProjectRepository(self.database_path).list_all()
            papers = SQLitePaperRepository(self.database_path).list_all()
        except sqlite3.OperationalError:
            return DashboardSnapshot()
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
        try:
            return SQLiteProjectRepository(self.database_path).list_all()
        except sqlite3.OperationalError:
            return ()

    def papers(self):
        if not self.database_path.exists():
            return ()
        try:
            return SQLitePaperRepository(self.database_path).list_all()
        except sqlite3.OperationalError:
            return ()

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
        return tuple(ScreeningRow(
            paper_id=row["paper_id"], title=row["title"], year=row["publication_year"],
            decision="Included" if row["included"] else "Excluded", reason=row["reason"],
            run_id=row["run_id"], criteria_version=row["criteria_version"],
        ) for row in rows)

    def screening_runs(self, limit: int = 100) -> tuple[ScreeningRunSnapshot, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT run_id, project_id, criteria_version, started_at, total_input, unique_papers, "
                    "duplicates_removed, screened_papers FROM screening_runs ORDER BY started_at DESC LIMIT ?",
                    (max(1, int(limit)),),
                ).fetchall()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(ScreeningRunSnapshot(
            run_id=row["run_id"], project_id=row["project_id"], criteria_version=row["criteria_version"],
            started_at=row["started_at"], total_input=row["total_input"], unique_papers=row["unique_papers"],
            duplicates_removed=row["duplicates_removed"], screened_papers=row["screened_papers"],
        ) for row in rows)

    def metadata_quality(self) -> MetadataQualitySnapshot:
        papers = self.papers()
        total = len(papers)
        return MetadataQualitySnapshot(
            total_papers=total,
            with_abstract=sum(bool(p.abstract and p.abstract.strip()) for p in papers),
            with_authors=sum(bool(p.authors) for p in papers),
            with_doi=sum(bool(p.doi and p.doi.strip()) for p in papers),
            with_pmid=sum(bool(p.pmid and p.pmid.strip()) for p in papers),
            with_journal=sum(bool(p.journal and p.journal.strip()) for p in papers),
            with_year=sum(p.publication_year is not None for p in papers),
        )

    def audit_rows(self, limit: int = 200) -> tuple[AuditRow, ...]:
        if not self.database_path.exists():
            return ()
        try:
            changes = SQLiteMetadataHistoryRepository(self.database_path).list_all()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(AuditRow(
            changed_at=change.changed_at.isoformat(), paper_id=str(change.paper_id),
            source_key=change.source_key, source_record_id=change.source_record_id,
            changed_fields=change.changed_fields,
        ) for change in changes[-limit:])

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
                "title": paper.title, "authors": ", ".join(paper.authors), "abstract": paper.abstract or "",
                "doi": paper.doi or "", "pmid": paper.pmid or "", "journal": paper.journal or "",
                "year": paper.publication_year or "", "provenance_count": int(provenance_count),
            }
        except (sqlite3.OperationalError, ValueError):
            return None

    def all_audits(self):
        if not self.database_path.exists():
            return ()
        try:
            return SQLiteScreeningAuditRepository(self.database_path).list_all()
        except sqlite3.OperationalError:
            return ()

    def rule_analysis(self) -> RuleAnalysis:
        return RuleAnalysis.from_audits(self.all_audits())

    def exclusion_reason_analysis(self) -> ExclusionReasonAnalysis:
        return ExclusionReasonAnalysis.from_audits(self.all_audits())

    def author_analysis(self) -> AuthorAnalysis:
        return AuthorAnalysis.from_papers(self.papers())

    def journal_analysis(self) -> JournalAnalysis:
        return JournalAnalysis.from_papers(self.papers())

    def publication_year_analysis(self) -> PublicationYearAnalysis:
        return PublicationYearAnalysis.from_papers(self.papers())

    def deduplication_analysis(self) -> DeduplicationAnalysis:
        runs = self.screening_runs(limit=100000)
        total_input = sum(run.total_input for run in runs)
        unique_papers = sum(run.unique_papers for run in runs)
        duplicates_removed = sum(run.duplicates_removed for run in runs)
        if total_input == 0:
            return DeduplicationAnalysis(total_input=0, unique_papers=0, duplicate_papers=0)
        return DeduplicationAnalysis(
            total_input=total_input, unique_papers=unique_papers, duplicate_papers=duplicates_removed,
        )

    def project(self, project_id: str):
        if not self.database_path.exists():
            return None
        try:
            return SQLiteProjectRepository(self.database_path).get(UUID(project_id))
        except (sqlite3.OperationalError, ValueError):
            return None

    def project_snapshot(self, project_id: str) -> ProjectSnapshot | None:
        project = self.project(project_id)
        if project is None:
            return None
        runs = tuple(run for run in self.screening_runs(limit=100000) if run.project_id == str(project.project_id))
        return ProjectSnapshot(
            project_id=str(project.project_id), name=project.name,
            research_question=project.research_question, topic=project.criteria.topic,
            inclusion=tuple(project.criteria.inclusion), exclusion=tuple(project.criteria.exclusion),
            created_at=project.created_at.isoformat(), screening_runs=len(runs),
            screened_papers=sum(run.screened_papers for run in runs),
        )

    def screening_detail(self, paper_id: str, run_id: str | None = None) -> ScreeningDetail | None:
        if not self.database_path.exists():
            return None
        try:
            with self._connect() as connection:
                if run_id:
                    row = connection.execute(
                        "SELECT sr.paper_id, p.title, sr.included, sr.reason, sr.run_id, sr.criteria_version "
                        "FROM screening_results sr JOIN papers p ON p.paper_id = sr.paper_id "
                        "WHERE sr.paper_id = ? AND sr.run_id = ? LIMIT 1", (paper_id, run_id),
                    ).fetchone()
                else:
                    row = connection.execute(
                        "SELECT sr.paper_id, p.title, sr.included, sr.reason, sr.run_id, sr.criteria_version "
                        "FROM screening_results sr JOIN papers p ON p.paper_id = sr.paper_id "
                        "WHERE sr.paper_id = ? ORDER BY rowid DESC LIMIT 1", (paper_id,),
                    ).fetchone()
            if row is None:
                return None
            audit = SQLiteScreeningAuditRepository(self.database_path).get(
                UUID(paper_id), UUID(row["run_id"]) if row["run_id"] else None
            )
        except (sqlite3.OperationalError, ValueError):
            return None
        return ScreeningDetail(
            paper_id=row["paper_id"], title=row["title"],
            decision="Included" if row["included"] else "Excluded", reason=row["reason"],
            run_id=row["run_id"], criteria_version=row["criteria_version"],
            matched_rules=tuple(audit.matched_rules) if audit else (),
            failed_rules=tuple(audit.failed_rules) if audit else (),
            audit_id=f"{row['run_id']}:{row['paper_id']}" if audit else None,
        )

    def sources(self) -> tuple[SourceSnapshot, ...]:
        try:
            config = load_scopus_environment()
            manager = ScopusConnectionManager(
                config.oauth, default_scopus_token_store(),
                oauth_client=ScopusOAuthClient(config.oauth) if config.oauth is not None else None,
                transport_config=config.transport,
            )
            registry = build_default_source_connection_registry(manager)
            return tuple(SourceSnapshot(
                state.source.key, state.source.display_name, state.status.value, state.detail
            ) for state in registry.inspect_all())
        except Exception as exc:
            return (SourceSnapshot("unknown", "Bibliographic sources", "error", str(exc)),)
