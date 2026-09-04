from uuid import uuid4

from psi_jarvis.application.screening.sensitivity import SensitivityAnalysisService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper


class SpyNormalizer(PaperNormalizer):
    def __init__(self):
        self.calls = 0

    def normalize(self, paper):
        self.calls += 1
        return super().normalize(paper)


class SpyDeduplicator(PaperDeduplicator):
    def __init__(self):
        self.calls = 0

    def deduplicate(self, papers):
        self.calls += 1
        return super().deduplicate(papers)


def make_paper(title: str, abstract: str) -> Paper:
    return Paper(
        id=uuid4(),
        title=title,
        authors=(),
        abstract=abstract,
        doi=None,
        pmid=None,
        publication_year=None,
        journal=None,
    )


def test_sensitivity_service_uses_injected_preparation_components():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
    )

    normalizer = SpyNormalizer()
    deduplicator = SpyDeduplicator()

    service = SensitivityAnalysisService(
        normalizer=normalizer,
        deduplicator=deduplicator,
    )

    service.execute(
        papers=papers,
        base_criteria=ScreeningCriteria(topic="cognition", inclusion=("memory",)),
        alternative_criteria=ScreeningCriteria(topic="cognition"),
    )

    assert normalizer.calls == 1
    assert deduplicator.calls == 1
