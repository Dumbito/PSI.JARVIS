from uuid import uuid4

from psi_jarvis.application.screening.rule_consistency import RuleConsistencyService
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


def test_rule_consistency_integration():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
        make_paper("Cognition only", "cognition"),
        make_paper("Other", "other"),
    )

    analysis = RuleConsistencyService().execute(
        papers=papers,
        criteria=ScreeningCriteria(
            topic="cognition",
            inclusion=("memory",),
        ),
    )

    assert analysis.total_results == 3
    assert analysis.included_results == 1
    assert analysis.excluded_results == 2
    assert analysis.consistent is True
