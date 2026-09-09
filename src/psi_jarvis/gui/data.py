from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from psi_jarvis.domain.analysis.author_analysis import AuthorAnalysis
from psi_jarvis.domain.analysis.deduplication_analysis import DeduplicationAnalysis
from psi_jarvis.domain.analysis.exclusion_reason_analysis import ExclusionReasonAnalysis
from psi_jarvis.domain.analysis.journal_analysis import JournalAnalysis
from psi_jarvis.domain.analysis.publication_year_analysis import PublicationYearAnalysis
from psi_jarvis.domain.analysis.rule_analysis import RuleAnalysis
from psi_jarvis.gui.formatting import format_timestamp
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
class ProjectPaperSnapshot:
    paper_id: str
    title: str
    year: int | None
    journal: str | None
    doi: str | None
    pmid: str | None
    position: int


@dataclass(frozen=True)
class ProjectProvenanceSnapshot:
    paper_id: str
    title: str
    batch_id: str
    source_key: str
    source_record_id: str | None
    record_ordinal: int
    format_name: str
    format_version: str
    mapping_version: str
    raw_record_sha256: str


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
            excluded=excluded, conflicts=0, source_counts=tuple(sorted(source_counts.items())),
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

    def sources(self) -> tuple[SourceSnapshot, ...]:
        """Return source connection state without exposing credentials or mutating state."""
        try:
            environment = load_scopus_environment()
            manager = ScopusConnectionManager(
                environment.oauth,
                default_scopus_token_store(),
                oauth_client=ScopusOAuthClient(environment.oauth) if environment.oauth else None,
                transport_config=environment.transport,
            )
            states = build_default_source_connection_registry(manager).inspect_all()
            return tuple(
                SourceSnapshot(
                    state.source.key,
                    state.source.display_name,
                    state.status.value,
                    state.detail or "",
                )
                for state in states
            )
        except Exception as exc:
            return (
                SourceSnapshot("pubmed", "PubMed", "available", "Public source without authentication."),
                SourceSnapshot("scopus", "Scopus", "unavailable", f"Scopus configuration could not be inspected: {exc}"),
                SourceSnapshot("web_of_science", "Web of Science", "unavailable", "Connector available, but no credential is configured."),
                SourceSnapshot("zotero", "Zotero", "unavailable", "Connector available, but no credential is configured."),
            )

    def screening_rows(self) -> tuple[ScreeningRow, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute("SELECT sr.paper_id, p.title, p.publication_year, sr.included, sr.reason, sr.run_id, sr.criteria_version FROM screening_results sr JOIN papers p ON p.paper_id = sr.paper_id ORDER BY p.title COLLATE NOCASE").fetchall()
        except sqlite3.OperationalError:
            return ()
        return tuple(ScreeningRow(row["paper_id"], row["title"], row["publication_year"], "Included" if row["included"] else "Excluded", row["reason"], row["run_id"], row["criteria_version"]) for row in rows)

    def screening_runs(self, limit: int = 100) -> tuple[ScreeningRunSnapshot, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute("SELECT run_id, project_id, criteria_version, started_at, total_input, unique_papers, duplicates_removed, screened_papers FROM screening_runs ORDER BY started_at DESC LIMIT ?", (max(1, int(limit)),)).fetchall()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(ScreeningRunSnapshot(row["run_id"], row["project_id"], row["criteria_version"], row["started_at"], row["total_input"], row["unique_papers"], row["duplicates_removed"], row["screened_papers"]) for row in rows)

    def metadata_quality(self) -> MetadataQualitySnapshot:
        papers = self.papers()
        total = len(papers)
        return MetadataQualitySnapshot(total, sum(bool(p.abstract and p.abstract.strip()) for p in papers), sum(bool(p.authors) for p in papers), sum(bool(p.doi and p.doi.strip()) for p in papers), sum(bool(p.pmid and p.pmid.strip()) for p in papers), sum(bool(p.journal and p.journal.strip()) for p in papers), sum(p.publication_year is not None for p in papers))

    def audit_rows(self, limit: int = 200) -> tuple[AuditRow, ...]:
        if not self.database_path.exists():
            return ()
        try:
            changes = SQLiteMetadataHistoryRepository(self.database_path).list_all()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(AuditRow(format_timestamp(change.changed_at), str(change.paper_id), change.source_key, change.source_record_id, change.changed_fields) for change in changes[-limit:])

    def paper_details(self, paper_id: str) -> dict[str, Any] | None:
        if not self.database_path.exists():
            return None
        try:
            paper = SQLitePaperRepository(self.database_path).get(UUID(paper_id))
            if paper is None:
                return None
            with self._connect() as connection:
                provenance_count = connection.execute("SELECT COUNT(*) FROM paper_provenances WHERE paper_id = ?", (paper_id,)).fetchone()[0]
            return {"paper_id": paper_id, "title": paper.title, "authors": ", ".join(paper.authors), "abstract": paper.abstract or "", "doi": paper.doi or "", "pmid": paper.pmid or "", "journal": paper.journal or "", "year": paper.publication_year or "", "provenance_count": int(provenance_count)}
        except (sqlite3.OperationalError, ValueError):
            return None

    def paper_provenance(self, paper_id: str) -> tuple[ProjectProvenanceSnapshot, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute("SELECT pp.paper_id,p.title,pp.batch_id,ab.source_key,pp.source_record_id,pp.record_ordinal,pp.format_name,pp.format_version,pp.mapping_version,pp.raw_record_sha256 FROM paper_provenances pp JOIN papers p ON p.paper_id=pp.paper_id JOIN acquisition_batches ab ON ab.batch_id=pp.batch_id WHERE pp.paper_id=? ORDER BY pp.record_ordinal", (paper_id,)).fetchall()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(ProjectProvenanceSnapshot(row["paper_id"], row["title"], row["batch_id"], row["source_key"], row["source_record_id"], row["record_ordinal"], row["format_name"], row["format_version"], row["mapping_version"], row["raw_record_sha256"]) for row in rows)

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
        total_input = sum(r.total_input for r in runs)
        unique = sum(r.unique_papers for r in runs)
        dup = sum(r.duplicates_removed for r in runs)
        return DeduplicationAnalysis(total_input=total_input, unique_papers=unique, duplicate_papers=dup)

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
        return ProjectSnapshot(str(project.project_id), project.name, project.research_question, project.criteria.topic, tuple(project.criteria.inclusion), tuple(project.criteria.exclusion), format_timestamp(project.created_at), len(runs), sum(run.screened_papers for run in runs))

    def project_papers(self, project_id: str) -> tuple[ProjectPaperSnapshot, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute("SELECT p.paper_id,p.title,p.publication_year,p.journal,p.doi,p.pmid,cp.position FROM corpora c JOIN corpus_papers cp ON cp.corpus_id=c.corpus_id JOIN papers p ON p.paper_id=cp.paper_id WHERE c.project_id=? ORDER BY cp.position", (project_id,)).fetchall()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(ProjectPaperSnapshot(row["paper_id"], row["title"], row["publication_year"], row["journal"], row["doi"], row["pmid"], row["position"]) for row in rows)

    def project_screening_rows(self, project_id: str) -> tuple[ScreeningRow, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute("SELECT sr.paper_id,p.title,p.publication_year,sr.included,sr.reason,sr.run_id,sr.criteria_version FROM screening_results sr JOIN papers p ON p.paper_id=sr.paper_id JOIN screening_runs run ON run.run_id=sr.run_id WHERE run.project_id=? ORDER BY p.title COLLATE NOCASE", (project_id,)).fetchall()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(ScreeningRow(row["paper_id"], row["title"], row["publication_year"], "Included" if row["included"] else "Excluded", row["reason"], row["run_id"], row["criteria_version"]) for row in rows)

    def project_provenance(self, project_id: str) -> tuple[ProjectProvenanceSnapshot, ...]:
        if not self.database_path.exists():
            return ()
        try:
            with self._connect() as connection:
                rows = connection.execute("SELECT pp.paper_id,p.title,pp.batch_id,ab.source_key,pp.source_record_id,pp.record_ordinal,pp.format_name,pp.format_version,pp.mapping_version,pp.raw_record_sha256 FROM corpora c JOIN corpus_papers cp ON cp.corpus_id=c.corpus_id JOIN paper_provenances pp ON pp.paper_id=cp.paper_id JOIN papers p ON p.paper_id=pp.paper_id JOIN acquisition_batches ab ON ab.batch_id=pp.batch_id WHERE c.project_id=? ORDER BY cp.position,pp.record_ordinal", (project_id,)).fetchall()
        except (sqlite3.OperationalError, ValueError):
            return ()
        return tuple(ProjectProvenanceSnapshot(row["paper_id"], row["title"], row["batch_id"], row["source_key"], row["source_record_id"], row["record_ordinal"], row["format_name"], row["format_version"], row["mapping_version"], row["raw_record_sha256"]) for row in rows)

    def screening_detail(self, paper_id: str, run_id: str | None = None) -> ScreeningDetail | None:
        if not self.database_path.exists():
            return None
        try:
            with self._connect() as connection:
                if run_id:
                    row = connection.execute("SELECT sr.paper_id,p.title,sr.included,sr.reason,sr.run_id,sr.criteria_version,sa.audit_key FROM screening_results sr JOIN papers p ON p.paper_id=sr.paper_id LEFT JOIN screening_audits sa ON sa.paper_id=sr.paper_id AND sa.run_id=sr.run_id WHERE sr.paper_id=? AND sr.run_id=? LIMIT 1", (paper_id, run_id)).fetchone()
                else:
                    row = connection.execute("SELECT sr.paper_id,p.title,sr.included,sr.reason,sr.run_id,sr.criteria_version,sa.audit_key FROM screening_results sr JOIN papers p ON p.paper_id=sr.paper_id LEFT JOIN screening_audits sa ON sa.paper_id=sr.paper_id AND sa.run_id=sr.run_id WHERE sr.paper_id=? ORDER BY rowid DESC LIMIT 1", (paper_id,)).fetchone()
            if row is None:
                return None
            audit = SQLiteScreeningAuditRepository(self.database_path).get(UUID(paper_id), UUID(row["run_id"]) if row["run_id"] else None)
        except (sqlite3.OperationalError, ValueError):
            return None
        return ScreeningDetail(row["paper_id"], row["title"], "Included" if row["included"] else "Excluded", row["reason"], row["run_id"], row["criteria_version"], tuple(audit.matched_rules) if audit else (), tuple(audit.failed_rules) if audit else (), str(row["audit_key"]) if row["audit_key"] else None)
