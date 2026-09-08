"""Orchestrates write actions triggered from the GUI.

This module never re-implements screening, deduplication, provenance or
synchronization logic. It only wires together the *same* application
services and SQLite repositories used by the CLI and the integration
tests (see ``tests/integration/test_review_project_end_to_end.py``), so
that anything created from the GUI is fully interoperable with the rest
of PSI.JARVIS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from psi_jarvis.application.acquisition import AcquisitionRequest, AcquisitionService
from psi_jarvis.application.pipeline.pipeline import PaperPipeline, PipelineResult
from psi_jarvis.application.project.create_review_project import CreateReviewProjectService
from psi_jarvis.application.project.screen_review_project import ScreenReviewProjectService
from psi_jarvis.application.reporting.export_report import ReportExporter
from psi_jarvis.domain.analysis.author_analysis import AuthorAnalysis
from psi_jarvis.domain.analysis.criteria_analysis import CriteriaAnalysis
from psi_jarvis.domain.analysis.decision_distribution import DecisionDistribution
from psi_jarvis.domain.analysis.deduplication_analysis import DeduplicationAnalysis
from psi_jarvis.domain.analysis.exclusion_reason_analysis import ExclusionReasonAnalysis
from psi_jarvis.domain.analysis.journal_analysis import JournalAnalysis
from psi_jarvis.domain.analysis.metadata_quality import MetadataQuality
from psi_jarvis.domain.analysis.publication_year_analysis import PublicationYearAnalysis
from psi_jarvis.domain.analysis.rule_analysis import RuleAnalysis
from psi_jarvis.domain.analysis.screening_metrics import ScreeningMetrics
from psi_jarvis.domain.analysis.statistics import StatisticalSummary
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.reporting import Report
from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.infrastructure.acquisition import RISImporter
from psi_jarvis.infrastructure.importers.csv_importer import CSVImporter
from psi_jarvis.infrastructure.importers.excel_importer import ExcelImporter
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository
from psi_jarvis.infrastructure.sqlite_screening_audit_repository import SQLiteScreeningAuditRepository
from psi_jarvis.infrastructure.sqlite_screening_execution_repository import (
    SQLiteScreeningExecutionRepository,
)
from psi_jarvis.infrastructure.sqlite_screening_result_repository import (
    SQLiteScreeningResultRepository,
)
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository


class UnsupportedFileFormat(ValueError):
    """Raised when the GUI is asked to import a file type with no registered adapter."""


@dataclass(frozen=True)
class ImportOutcome:
    """Human-facing summary of a GUI-triggered import + screening run."""

    run_id: str
    total_input: int
    unique_papers: int
    duplicates_removed: int
    screened_papers: int
    included: int
    excluded: int


def _acquisition_port(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".ris":
        return RISImporter()
    if suffix == ".csv":
        return CSVImporter()
    if suffix in {".xlsx", ".xls"}:
        return ExcelImporter()
    raise UnsupportedFileFormat(f"Formato de archivo no soportado: {suffix or '(sin extensión)'}")


class GuiWorkflowService:
    """Write-side counterpart of :class:`GuiDataService`.

    Every method here delegates to an existing application service or
    infrastructure repository. No screening, deduplication or
    synchronization rule is decided inside this class or inside any
    widget that calls it.
    """

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    # -- Projects ---------------------------------------------------

    def create_project(
        self,
        name: str,
        research_question: str,
        topic: str,
        inclusion: tuple[str, ...],
        exclusion: tuple[str, ...],
    ):
        criteria = ScreeningCriteria(topic=topic, inclusion=inclusion, exclusion=exclusion)
        repository = SQLiteProjectRepository(self.database_path)
        return CreateReviewProjectService(repository).execute(
            name=name, criteria=criteria, research_question=research_question,
        )

    # -- Acquisition + screening -------------------------------------

    def import_and_screen(self, project_id: UUID, file_path: str | Path) -> ImportOutcome:
        path = Path(file_path)
        acquisition = AcquisitionService(_acquisition_port(path)).execute(
            AcquisitionRequest(location=str(path))
        )
        if not acquisition.success:
            message = (
                acquisition.issues[0].message if acquisition.issues else "No se pudo importar el archivo."
            )
            raise ValueError(message)
        if not acquisition.papers:
            raise ValueError("El archivo no contiene artículos reconocibles.")

        paper_repository = SQLitePaperRepository(self.database_path)
        for paper in acquisition.papers:
            paper_repository.save(paper)

        pipeline = PaperPipeline(
            run_repository=SQLiteScreeningRunRepository(self.database_path),
            result_repository=SQLiteScreeningResultRepository(self.database_path),
            audit_repository=SQLiteScreeningAuditRepository(self.database_path),
            execution_repository=SQLiteScreeningExecutionRepository(self.database_path),
        )
        project_repository = SQLiteProjectRepository(self.database_path)
        result: PipelineResult = ScreenReviewProjectService(project_repository, pipeline).execute(
            project_id, acquisition.papers,
        )

        # Deduplication/normalization may have produced canonical paper
        # records distinct from the raw acquisition; persist those too so
        # Screening/Papers pages resolve to the exact rows the engine saw.
        for paper in result.papers:
            paper_repository.save(paper)

        included = sum(1 for item in result.screening_results if item.included)
        return ImportOutcome(
            run_id=str(result.run.run_id),
            total_input=result.total_input,
            unique_papers=result.unique_papers,
            duplicates_removed=result.duplicates_removed,
            screened_papers=result.screened_papers,
            included=included,
            excluded=result.screened_papers - included,
        )

    # -- Reporting ----------------------------------------------------

    def report_for_run(self, run_id: UUID, title: str = "PSI.JARVIS Screening Report") -> Report | None:
        """Assembles a :class:`Report` for an already-persisted run.

        Every section is produced by the same domain analysis classmethods
        (``RuleAnalysis.from_audits`` and friends) the pipeline itself uses;
        this only re-hydrates their inputs from SQLite instead of from a
        just-executed in-memory run.
        """
        all_audits = SQLiteScreeningAuditRepository(self.database_path).list_all()
        audits: tuple[ScreeningAudit, ...] = tuple(a for a in all_audits if a.run_id == run_id)
        if not audits:
            return None

        run = SQLiteScreeningRunRepository(self.database_path).get(run_id)
        paper_repository = SQLitePaperRepository(self.database_path)
        papers = tuple(
            paper for paper in (paper_repository.get(a.paper_id) for a in audits) if paper is not None
        )

        included = sum(1 for a in audits if a.included)
        excluded = len(audits) - included
        screened_papers = len(audits)
        if run is not None:
            total_input = run.total_input
            duplicates_removed = run.duplicates_removed
            unique_papers = run.unique_papers
        else:
            total_input = screened_papers
            duplicates_removed = 0
            unique_papers = screened_papers

        statistics = StatisticalSummary(
            total_input=total_input, unique_papers=unique_papers,
            duplicates_removed=duplicates_removed, screened_papers=screened_papers,
            included_papers=included, excluded_papers=excluded,
        )
        screening_metrics = ScreeningMetrics.from_audits(
            total_input=total_input, screened_papers=screened_papers,
            included_papers=included, excluded_papers=excluded,
            duplicates_removed=duplicates_removed, audits=audits,
        )
        return Report(
            title=title,
            statistics=statistics,
            screening_metrics=screening_metrics,
            rule_analysis=RuleAnalysis.from_audits(audits),
            criteria_analysis=CriteriaAnalysis.from_audits(audits),
            decision_distribution=DecisionDistribution(total=screened_papers, included=included, excluded=excluded),
            exclusion_reason_analysis=ExclusionReasonAnalysis.from_audits(audits),
            metadata_quality=MetadataQuality.from_papers(papers),
            deduplication_analysis=DeduplicationAnalysis(
                total_input=total_input, unique_papers=unique_papers, duplicate_papers=duplicates_removed,
            ),
            author_analysis=AuthorAnalysis.from_papers(papers),
            journal_analysis=JournalAnalysis.from_papers(papers),
            publication_year_analysis=PublicationYearAnalysis.from_papers(papers),
        )

    def export_report(self, run_id: UUID, output_dir: str | Path) -> tuple[Path, Path] | None:
        report = self.report_for_run(run_id)
        if report is None:
            return None
        exporter = ReportExporter(output_dir=Path(output_dir))
        return exporter.export_json(report), exporter.export_markdown(report)
