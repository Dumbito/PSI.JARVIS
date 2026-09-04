from uuid import uuid4

from psi_jarvis.domain.analysis.configuration_comparison import (
    ConfigurationComparison,
)
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.engine import ScreeningEngine


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


def test_configuration_comparison_profiles_multiple_configurations():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
        make_paper("Cognition only", "cognition"),
        make_paper("Memory only", "memory"),
    )

    configurations = (
        ScreeningCriteria(
            topic="cognition",
            inclusion=("memory",),
        ),
        ScreeningCriteria(
            topic="cognition",
        ),
        ScreeningCriteria(
            topic="memory",
        ),
    )

    runs = tuple(
        (
            criteria,
            tuple(
                ScreeningEngine(criteria).evaluate(paper)
                for paper in papers
            ),
        )
        for criteria in configurations
    )

    comparison = ConfigurationComparison.from_runs(runs)

    assert comparison.configuration_count == 3
    assert comparison.total_papers == 3
    assert comparison.minimum_included == 1
    assert comparison.maximum_included == 2
    assert comparison.included_range == 1
    assert len(comparison.profiles) == 3


def test_configuration_comparison_rejects_different_paper_sets():
    paper_a = make_paper("Cognition", "cognition")
    paper_b = make_paper("Memory", "memory")

    criteria_a = ScreeningCriteria(topic="cognition")
    criteria_b = ScreeningCriteria(topic="memory")

    runs = (
        (
            criteria_a,
            (ScreeningEngine(criteria_a).evaluate(paper_a),),
        ),
        (
            criteria_b,
            (ScreeningEngine(criteria_b).evaluate(paper_b),),
        ),
    )

    try:
        ConfigurationComparison.from_runs(runs)
    except ValueError as exc:
        assert str(exc) == "All configurations must contain the same papers"
    else:
        raise AssertionError("Different paper sets must be rejected")
