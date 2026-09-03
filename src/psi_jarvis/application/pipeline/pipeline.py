from dataclasses import dataclass

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.analysis.statistics import StatisticalSummary
from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.domain.screening.audit_repository import ScreeningAuditRepository
from psi_jarvis.domain.screening.audit_report import ScreeningAuditReport
from psi_jarvis.domain.screening.engine import ScreeningEngine
from psi_jarvis.domain.screening.execution import ScreeningExecution
from psi_jarvis.domain.screening.execution_repository import ScreeningExecutionRepository
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.result_repository import ScreeningResultRepository
from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.domain.screening.run_repository import ScreeningRunRepository
from psi_jarvis.infrastructure.screening_audit_repository import InMemoryScreeningAuditRepository
from psi_jarvis.infrastructure.screening_result_repository import InMemoryScreeningResultRepository
from psi_jarvis.infrastructure.screening_run_repository import InMemoryScreeningRunRepository
from psi_jarvis.infrastructure.screening_execution_repository import InMemoryScreeningExecutionRepository


@dataclass(frozen=True)
class PipelineResult:
    papers: tuple[Paper, ...]
    screening_results: tuple[ScreeningResult, ...]
    audits: tuple[ScreeningAudit, ...]
    audit_report: ScreeningAuditReport
    total_input: int
    unique_papers: int
    duplicates_removed: int
    screened_papers: int
    run: ScreeningRun
    statistics: StatisticalSummary


class PaperPipeline:
    def __init__(
        self,
        normalizer: PaperNormalizer | None = None,
        deduplicator: PaperDeduplicator | None = None,
        screening_engine: ScreeningEngine | None = None,
        run_repository: ScreeningRunRepository | None = None,
        result_repository: ScreeningResultRepository | None = None,
        audit_repository: ScreeningAuditRepository | None = None,
        execution_repository: ScreeningExecutionRepository | None = None,
    ) -> None:
        self.normalizer = normalizer or PaperNormalizer()
        self.deduplicator = deduplicator or PaperDeduplicator()
        self.screening_engine = screening_engine
        self.run_repository = run_repository or InMemoryScreeningRunRepository()
        self.result_repository = result_repository or InMemoryScreeningResultRepository()
        self.audit_repository = audit_repository or InMemoryScreeningAuditRepository()
        self.execution_repository = execution_repository or InMemoryScreeningExecutionRepository()

    def process(
        self,
        papers: list[Paper] | tuple[Paper, ...],
        criteria: ScreeningCriteria,
        project_id: UUID | None = None,
    ) -> PipelineResult:
        total_input = len(papers)

        normalized_papers = tuple(
            self.normalizer.normalize(paper)
            for paper in papers
        )

        deduplication = self.deduplicator.deduplicate(normalized_papers)

        engine = self.screening_engine or ScreeningEngine(criteria)

        run = ScreeningRun.create(
            criteria_version=engine.criteria_version,
            project_id=project_id,
            total_input=total_input,
            unique_papers=deduplication.unique_papers,
            duplicates_removed=deduplication.duplicates_removed,
            screened_papers=len(deduplication.papers),
        )

        screening_results = tuple(
            engine.evaluate(paper).with_run_id(run.run_id)
            for paper in deduplication.papers
        )

        audits = tuple(
            ScreeningAudit.from_result(result)
            for result in screening_results
        )

        execution = ScreeningExecution(
            run=run,
            results=screening_results,
            audits=audits,
        )

        for result in screening_results:
            self.result_repository.save(result)

        for audit in audits:
            self.audit_repository.save(audit)

        audit_report = ScreeningAuditReport.from_audits(audits)

        statistics = StatisticalSummary(
            total_input=total_input,
            unique_papers=deduplication.unique_papers,
            duplicates_removed=deduplication.duplicates_removed,
            screened_papers=len(screening_results),
            included_papers=sum(1 for result in screening_results if result.included),
            excluded_papers=sum(1 for result in screening_results if not result.included),
        )

        self.run_repository.save(run)
        self.execution_repository.save(execution)

        return PipelineResult(
            papers=deduplication.papers,
            screening_results=screening_results,
            audits=audits,
            audit_report=audit_report,
            statistics=statistics,
            total_input=total_input,
            unique_papers=deduplication.unique_papers,
            duplicates_removed=deduplication.duplicates_removed,
            screened_papers=len(screening_results),
            run=run,
        )
