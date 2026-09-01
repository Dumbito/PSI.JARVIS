from dataclasses import dataclass

from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.screening.engine import ScreeningEngine
from psi_jarvis.domain.screening.result import ScreeningResult


@dataclass(frozen=True)
class PipelineResult:
    papers: tuple[Paper, ...]
    screening_results: tuple[ScreeningResult, ...]
    total_input: int
    unique_papers: int
    duplicates_removed: int
    screened_papers: int


class PaperPipeline:
    def __init__(
        self,
        normalizer: PaperNormalizer | None = None,
        deduplicator: PaperDeduplicator | None = None,
        screening_engine: ScreeningEngine | None = None,
    ) -> None:
        self.normalizer = normalizer or PaperNormalizer()
        self.deduplicator = deduplicator or PaperDeduplicator()
        self.screening_engine = screening_engine

    def process(
        self,
        papers: list[Paper] | tuple[Paper, ...],
        criteria: ScreeningCriteria,
    ) -> PipelineResult:
        total_input = len(papers)

        normalized_papers = tuple(
            self.normalizer.normalize(paper)
            for paper in papers
        )

        deduplication = self.deduplicator.deduplicate(normalized_papers)

        engine = self.screening_engine or ScreeningEngine(criteria)

        screening_results = tuple(
            engine.evaluate(paper)
            for paper in deduplication.papers
        )

        return PipelineResult(
            papers=deduplication.papers,
            screening_results=screening_results,
            total_input=total_input,
            unique_papers=deduplication.unique_papers,
            duplicates_removed=deduplication.duplicates_removed,
            screened_papers=len(screening_results),
        )
