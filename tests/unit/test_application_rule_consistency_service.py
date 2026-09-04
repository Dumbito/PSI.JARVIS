from uuid import uuid4

from psi_jarvis.application.screening.rule_consistency import RuleConsistencyService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def make_paper(title: str, abstract: str, doi: str | None = None) -> Paper:
    return Paper(
        id=uuid4(),
        title=title,
        authors=(),
        abstract=abstract,
        doi=doi,
        pmid=None,
        publication_year=None,
        journal=None,
    )


def test_rule_consistency_service_uses_prepared_corpus():
    papers = (
        make_paper("Cognition", "cognition", "10.1000/example"),
        make_paper("Duplicate", "cognition", "10.1000/example"),
        make_paper("Memory", "memory"),
    )

    analysis = RuleConsistencyService().execute(
        papers=papers,
        criteria=ScreeningCriteria(topic="cognition"),
    )

    assert analysis.total_results == 2
    assert analysis.criteria_version
