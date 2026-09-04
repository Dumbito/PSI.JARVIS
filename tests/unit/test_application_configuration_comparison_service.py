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


def test_configuration_comparison_service_compares_all_configurations():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
        make_paper("Cognition only", "cognition"),
        make_paper("Memory only", "memory"),
    )

    configurations = (
        ScreeningCriteria(topic="cognition", inclusion=("memory",)),
        ScreeningCriteria(topic="cognition"),
        ScreeningCriteria(topic="memory"),
    )

    comparison = ConfigurationComparisonService().execute(
        papers=papers,
        configurations=configurations,
    )

    assert comparison.configuration_count == 3
    assert comparison.total_papers == 3
    assert comparison.included_range == 1


def test_configuration_comparison_service_deduplicates_once():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
        make_paper("Duplicate cognition", "cognition memory"),
    )

    from dataclasses import replace
    papers = (
        replace(papers[0], doi="10.1000/example"),
        replace(papers[1], doi="10.1000/example"),
    )

    configurations = (
        ScreeningCriteria(topic="cognition"),
        ScreeningCriteria(topic="memory"),
    )

    comparison = ConfigurationComparisonService().execute(
        papers=papers,
        configurations=configurations,
    )

    assert comparison.total_papers == 1
