from uuid import uuid4

from psi_jarvis.application.screening.sensitivity import SensitivityAnalysisService
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


def test_sensitivity_service_compares_two_criteria_on_same_deduplicated_corpus():
    papers = (
        make_paper("Cognition and memory", "cognition memory", "10.1000/test"),
        make_paper("Duplicate", "cognition memory", "10.1000/test"),
        make_paper("Cognition only", "cognition"),
    )

    base_criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=("memory",),
    )
    alternative_criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=(),
    )

    analysis = SensitivityAnalysisService().execute(
        papers=papers,
        base_criteria=base_criteria,
        alternative_criteria=alternative_criteria,
    )

    assert analysis.total_papers == 2
    assert analysis.base_included == 1
    assert analysis.base_excluded == 1
    assert analysis.alternative_included == 2
    assert analysis.alternative_excluded == 0
    assert analysis.changed_decisions == 1
    assert analysis.newly_included == 1


def test_sensitivity_service_reuses_normalization_and_deduplication():
    papers = (
        make_paper("Cognition and memory", "cognition memory", "10.1000/TEST"),
        make_paper("Same paper", "cognition memory", "https://doi.org/10.1000/test"),
    )

    criteria = ScreeningCriteria(topic="cognition", inclusion=("memory",))

    analysis = SensitivityAnalysisService().execute(
        papers=papers,
        base_criteria=criteria,
        alternative_criteria=ScreeningCriteria(topic="cognition", inclusion=()),
    )

    assert analysis.total_papers == 1
