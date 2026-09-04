from uuid import uuid4
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.analysis.sensitivity_analysis import SensitivityAnalysis


def test_sensitivity_analysis_records_criteria_versions():
    paper_id = uuid4()

    base_results = (
        ScreeningResult(
            paper_id=paper_id,
            included=True,
            reason="base include",
            criteria_version="base-v1",
        ),
    )
    alternative_results = (
        ScreeningResult(
            paper_id=paper_id,
            included=False,
            reason="alternative exclude",
            criteria_version="alternative-v2",
        ),
    )

    analysis = SensitivityAnalysis.from_results(
        base_results=base_results,
        alternative_results=alternative_results,
    )

    assert analysis.base_criteria_version == "base-v1"
    assert analysis.alternative_criteria_version == "alternative-v2"


def test_sensitivity_analysis_rejects_same_criteria_version():
    paper_id = uuid4()

    base_results = (
        ScreeningResult(
            paper_id=paper_id,
            included=True,
            reason="base include",
            criteria_version="same-version",
        ),
    )
    alternative_results = (
        ScreeningResult(
            paper_id=paper_id,
            included=False,
            reason="alternative exclude",
            criteria_version="same-version",
        ),
    )

    try:
        SensitivityAnalysis.from_results(
            base_results=base_results,
            alternative_results=alternative_results,
        )
    except ValueError as exc:
        assert str(exc) == "Base and alternative criteria versions must differ"
    else:
        raise AssertionError("Identical criteria versions must be rejected")


def test_sensitivity_analysis_rejects_mixed_base_versions():
    paper_id_a = uuid4()
    paper_id_b = uuid4()

    base_results = (
        ScreeningResult(
            paper_id=paper_id_a,
            included=True,
            reason="base include",
            criteria_version="base-v1",
        ),
        ScreeningResult(
            paper_id=paper_id_b,
            included=False,
            reason="base exclude",
            criteria_version="base-v2",
        ),
    )
    alternative_results = (
        ScreeningResult(
            paper_id=paper_id_a,
            included=True,
            reason="alternative include",
            criteria_version="alternative-v1",
        ),
        ScreeningResult(
            paper_id=paper_id_b,
            included=False,
            reason="alternative exclude",
            criteria_version="alternative-v1",
        ),
    )

    try:
        SensitivityAnalysis.from_results(
            base_results=base_results,
            alternative_results=alternative_results,
        )
    except ValueError as exc:
        assert str(exc) == "Base results must use a single criteria version"
    else:
        raise AssertionError("Mixed base criteria versions must be rejected")



def test_sensitivity_analysis_rejects_duplicate_base_papers():
    paper_id = uuid4()

    result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="base include",
        criteria_version="base-v1",
    )

    alternative_result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="alternative include",
        criteria_version="alternative-v1",
    )

    try:
        SensitivityAnalysis.from_results(
            base_results=(result, result),
            alternative_results=(alternative_result,),
        )
    except ValueError as exc:
        assert str(exc) == "Base results must not contain duplicate papers"
    else:
        raise AssertionError("Duplicate base papers must be rejected")


def test_sensitivity_analysis_rejects_duplicate_alternative_papers():
    paper_id = uuid4()

    base_result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="base include",
        criteria_version="base-v1",
    )

    result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="alternative include",
        criteria_version="alternative-v1",
    )

    try:
        SensitivityAnalysis.from_results(
            base_results=(base_result,),
            alternative_results=(result, result),
        )
    except ValueError as exc:
        assert str(exc) == "Alternative results must not contain duplicate papers"
    else:
        raise AssertionError("Duplicate alternative papers must be rejected")
