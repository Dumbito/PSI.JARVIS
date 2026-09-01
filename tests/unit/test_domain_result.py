from uuid import uuid4

from psi_jarvis.domain.screening.result import ScreeningResult


def test_screening_result_include():
    paper_id = uuid4()

    result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="Paper matches screening criteria",
        matched_rules=("intelligence",),
    )

    assert result.paper_id == paper_id
    assert result.included is True
    assert result.status == "include"
    assert result.matched_rules == ("intelligence",)


def test_screening_result_exclude():
    paper_id = uuid4()

    result = ScreeningResult(
        paper_id=paper_id,
        included=False,
        reason="Topic not found",
        failed_rules=("intelligence",),
    )

    assert result.included is False
    assert result.status == "exclude"
    assert result.failed_rules == ("intelligence",)


def test_screening_result_is_immutable():
    result = ScreeningResult(
        paper_id=uuid4(),
        included=True,
        reason="ok",
    )

    try:
        result.included = False
        assert False
    except AttributeError:
        pass
