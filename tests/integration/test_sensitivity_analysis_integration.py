from uuid import uuid4

from psi_jarvis.domain.analysis.sensitivity_analysis import SensitivityAnalysis
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


def test_sensitivity_analysis_between_screening_criteria():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
        make_paper("Cognition only", "cognition"),
        make_paper("Memory study", "memory"),
    )

    base_criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=("memory",),
    )
    alternative_criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=(),
    )

    base_engine = ScreeningEngine(base_criteria)
    alternative_engine = ScreeningEngine(alternative_criteria)

    base_results = tuple(base_engine.evaluate(paper) for paper in papers)
    alternative_results = tuple(
        alternative_engine.evaluate(paper) for paper in papers
    )

    analysis = SensitivityAnalysis.from_results(
        base_results=base_results,
        alternative_results=alternative_results,
    )

    assert analysis.total_papers == 3
    assert analysis.base_included == 1
    assert analysis.base_excluded == 2
    assert analysis.alternative_included == 2
    assert analysis.alternative_excluded == 1
    assert analysis.changed_decisions == 1
    assert analysis.newly_included == 1
    assert analysis.newly_excluded == 0
    assert analysis.unchanged_decisions == 2


def test_sensitivity_analysis_rejects_different_paper_sets():
    paper_a = make_paper("Cognition", "cognition")
    paper_b = make_paper("Memory", "memory")

    criteria = ScreeningCriteria(topic="cognition")
    engine = ScreeningEngine(criteria)

    base_results = (engine.evaluate(paper_a),)
    alternative_results = (engine.evaluate(paper_b),)

    try:
        SensitivityAnalysis.from_results(
            base_results=base_results,
            alternative_results=alternative_results,
        )
    except ValueError as exc:
        assert str(exc) == "Base and alternative results must contain the same papers"
    else:
        raise AssertionError("Different paper sets must be rejected")
