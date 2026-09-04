from dataclasses import dataclass

from psi_jarvis.application.pipeline.pipeline import PipelineResult
from psi_jarvis.domain.reporting import Report


@dataclass(frozen=True)
class ReportBuilder:
    title: str = "PSI.JARVIS Screening Report"

    def execute(self, result: PipelineResult) -> Report:
        return Report(
            title=self.title,
            statistics=result.statistics,
            screening_metrics=result.screening_metrics,
            rule_analysis=result.rule_analysis,
            criteria_analysis=result.criteria_analysis,
            decision_distribution=result.decision_distribution,
            exclusion_reason_analysis=result.exclusion_reason_analysis,
            metadata_quality=result.metadata_quality,
            deduplication_analysis=result.deduplication_analysis,
            author_analysis=result.author_analysis,
            journal_analysis=result.journal_analysis,
            publication_year_analysis=result.publication_year_analysis,
        )
