from dataclasses import dataclass

from psi_jarvis.domain.analysis.rule_consistency import RuleConsistency
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.engine import ScreeningEngine


@dataclass(frozen=True)
class RuleConsistencyService:
    normalizer: PaperNormalizer | None = None
    deduplicator: PaperDeduplicator | None = None

    def execute(
        self,
        papers: list[Paper] | tuple[Paper, ...],
        criteria: ScreeningCriteria,
    ) -> RuleConsistency:
        normalizer = self.normalizer or PaperNormalizer()
        deduplicator = self.deduplicator or PaperDeduplicator()

        normalized_papers = tuple(normalizer.normalize(paper) for paper in papers)
        corpus = deduplicator.deduplicate(normalized_papers).papers

        engine = ScreeningEngine(criteria)
        results = tuple(engine.evaluate(paper) for paper in corpus)

        return RuleConsistency.from_results(
            criteria=criteria,
            results=results,
        )
