from uuid import uuid4

from psi_jarvis.domain.analysis.sensitivity_analysis import SensitivityAnalysis

from psi_jarvis.domain.screening.result import ScreeningResult


def test_sensitivity_analysis_counts_decision_changes():
    paper_a = uuid4()
    paper_b = uuid4()
    paper_c = uuid4()

    base_results = (
        ScreeningResult(paper_id=paper_a, included=True, reason="base include", criteria_version="base-v1"),
        ScreeningResult(paper_id=paper_b, included=False, reason="base exclude", criteria_version="base-v1"),
        ScreeningResult(paper_id=paper_c, included=False, reason="base exclude", criteria_version="base-v1"),
    )

    alternative_results = (
        ScreeningResult(paper_id=paper_a, included=False, reason="alternative exclude", criteria_version="alternative-v2"),
        ScreeningResult(paper_id=paper_b, included=True, reason="alternative include", criteria_version="alternative-v2"),
        ScreeningResult(paper_id=paper_c, included=False, reason="alternative exclude", criteria_version="alternative-v2"),
    )

    analysis = SensitivityAnalysis.from_results(
        base_results=base_results,
        alternative_results=alternative_results,
    )

    assert analysis.total_papers == 3
    assert analysis.base_included == 1
    assert analysis.base_excluded == 2
    assert analysis.alternative_included == 1
    assert analysis.alternative_excluded == 2
    assert analysis.changed_decisions == 2
    assert analysis.newly_included == 1
    assert analysis.newly_excluded == 1
    assert analysis.unchanged_decisions == 1


def test_sensitivity_analysis_rejects_empty_results():
    try:
        SensitivityAnalysis.from_results(
            base_results=(),
            alternative_results=(),
        )
    except ValueError as exc:
        assert str(exc) == "Base results must use a single criteria version"
    else:
        raise AssertionError("Empty results must be rejected")


def test_sensitivity_analysis_is_frozen():
    analysis = SensitivityAnalysis(
        base_criteria_version="base-v1",
        alternative_criteria_version="alternative-v2",
        total_papers=1,
        base_included=1,
        base_excluded=0,
        alternative_included=1,
        alternative_excluded=0,
        changed_decisions=0,
        newly_included=0,
        newly_excluded=0,
        unchanged_decisions=1,
    )

    try:
        analysis.total_papers = 2
    except AttributeError:
        pass
    else:
        raise AssertionError("SensitivityAnalysis must be immutable")
