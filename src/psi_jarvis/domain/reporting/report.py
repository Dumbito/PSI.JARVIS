from dataclasses import dataclass

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


@dataclass(frozen=True)
class Report:
    title: str
    statistics: StatisticalSummary
    screening_metrics: ScreeningMetrics
    rule_analysis: RuleAnalysis
    criteria_analysis: CriteriaAnalysis
    decision_distribution: DecisionDistribution
    exclusion_reason_analysis: ExclusionReasonAnalysis
    metadata_quality: MetadataQuality
    deduplication_analysis: DeduplicationAnalysis
    author_analysis: AuthorAnalysis
    journal_analysis: JournalAnalysis
    publication_year_analysis: PublicationYearAnalysis

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Report title cannot be empty")

    @property
    def section_count(self) -> int:
        return 11

    def section(self, name: str) -> object | None:
        sections = {
            "statistics": self.statistics,
            "screening_metrics": self.screening_metrics,
            "rule_analysis": self.rule_analysis,
            "criteria_analysis": self.criteria_analysis,
            "decision_distribution": self.decision_distribution,
            "exclusion_reason_analysis": self.exclusion_reason_analysis,
            "metadata_quality": self.metadata_quality,
            "deduplication_analysis": self.deduplication_analysis,
            "author_analysis": self.author_analysis,
            "journal_analysis": self.journal_analysis,
            "publication_year_analysis": self.publication_year_analysis,
        }
        return sections.get(name)
