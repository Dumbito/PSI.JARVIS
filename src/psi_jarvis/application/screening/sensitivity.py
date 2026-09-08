from dataclasses import dataclass

from psi_jarvis.domain.analysis.sensitivity_analysis import SensitivityAnalysis
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.engine import ScreeningEngine


@dataclass(frozen=True)
class SensitivityAnalysisService:
    """Compara dos configuraciones de cribado sobre el mismo corpus preparado."""

    normalizer: PaperNormalizer | None = None
    deduplicator: PaperDeduplicator | None = None

    def execute(
        self,
        papers: list[Paper] | tuple[Paper, ...],
        base_criteria: ScreeningCriteria,
        alternative_criteria: ScreeningCriteria,
    ) -> SensitivityAnalysis:
        normalizer = self.normalizer or PaperNormalizer()
        deduplicator = self.deduplicator or PaperDeduplicator()

        normalized_papers = tuple(normalizer.normalize(paper) for paper in papers)
        corpus = deduplicator.deduplicate(normalized_papers).papers

        base_engine = ScreeningEngine(base_criteria)
        alternative_engine = ScreeningEngine(alternative_criteria)

        base_results = tuple(base_engine.evaluate(paper) for paper in corpus)
        alternative_results = tuple(
            alternative_engine.evaluate(paper) for paper in corpus
        )

        return SensitivityAnalysis.from_results(
            base_results=base_results,
            alternative_results=alternative_results,
        )
