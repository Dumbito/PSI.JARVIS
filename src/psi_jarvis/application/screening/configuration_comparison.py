from dataclasses import dataclass

from psi_jarvis.domain.analysis.configuration_comparison import (
    ConfigurationComparison,
)
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.engine import ScreeningEngine


@dataclass(frozen=True)
class ConfigurationComparisonService:
    normalizer: PaperNormalizer | None = None
    deduplicator: PaperDeduplicator | None = None

    def execute(
        self,
        papers: list[Paper] | tuple[Paper, ...],
        configurations: tuple[ScreeningCriteria, ...],
    ) -> ConfigurationComparison:
        if len(configurations) < 2:
            raise ValueError(
                "Configuration comparison requires at least two configurations"
            )

        normalizer = self.normalizer or PaperNormalizer()
        deduplicator = self.deduplicator or PaperDeduplicator()

        normalized_papers = tuple(
            normalizer.normalize(paper)
            for paper in papers
        )
        corpus = deduplicator.deduplicate(normalized_papers).papers

        runs = []

        for criteria in configurations:
            engine = ScreeningEngine(criteria)
            results = tuple(
                engine.evaluate(paper)
                for paper in corpus
            )
            runs.append((criteria, results))

        return ConfigurationComparison.from_runs(tuple(runs))
