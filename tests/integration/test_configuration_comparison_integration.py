from uuid import uuid4

from psi_jarvis.application.screening.configuration_comparison import (
    ConfigurationComparisonService,
)
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


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


def test_configuration_comparison_integration():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
        make_paper("Cognition only", "cognition"),
        make_paper("Memory only", "memory"),
    )

    comparison = ConfigurationComparisonService().execute(
        papers=papers,
        configurations=(
            ScreeningCriteria(topic="cognition"),
            ScreeningCriteria(topic="memory"),
        ),
    )

    assert comparison.configuration_count == 2
    assert comparison.total_papers == 3
    assert comparison.profiles[0].included_papers in (1, 2)
    assert comparison.profiles[1].included_papers in (1, 2)
