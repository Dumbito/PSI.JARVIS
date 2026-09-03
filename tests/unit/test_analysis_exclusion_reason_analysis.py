from uuid import uuid4

from psi_jarvis.domain.analysis.exclusion_reason_analysis import ExclusionReasonAnalysis
from psi_jarvis.domain.screening.audit import ScreeningAudit


def make_audit(included: bool, reason: str) -> ScreeningAudit:
    return ScreeningAudit(
        paper_id=uuid4(),
        included=included,
        reason=reason,
    )


def test_exclusion_reason_analysis_counts_and_rates():
    audits = (
        make_audit(False, "Animal study"),
        make_audit(False, "Animal study"),
        make_audit(False, "Wrong population"),
        make_audit(True, ""),
    )

    analysis = ExclusionReasonAnalysis.from_audits(audits)

    assert analysis.total_reasons == 2
    assert analysis.total_excluded == 3
    assert analysis.by_reason("Animal study").count == 2
    assert analysis.by_reason("Animal study").rate == 2 / 3
    assert analysis.by_reason("Wrong population").count == 1
    assert analysis.by_reason("Wrong population").rate == 1 / 3


def test_exclusion_reason_analysis_empty_audits():
    analysis = ExclusionReasonAnalysis.from_audits(())
    assert analysis.total_reasons == 0
    assert analysis.total_excluded == 0


def test_exclusion_reason_analysis_ignores_included_audits():
    audits = (
        make_audit(True, "Should not count"),
        make_audit(False, "Valid reason"),
    )
    analysis = ExclusionReasonAnalysis.from_audits(audits)
    assert analysis.total_excluded == 1
    assert analysis.by_reason("Should not count") is None
    assert analysis.by_reason("Valid reason").count == 1


def test_exclusion_reason_statistics_rejects_invalid_values():
    from psi_jarvis.domain.analysis.exclusion_reason_analysis import ExclusionReasonStatistics

    try:
        ExclusionReasonStatistics("", 1, 1)
    except ValueError as exc:
        assert str(exc) == "Exclusion reason cannot be empty"
    else:
        raise AssertionError("Expected ValueError")

    try:
        ExclusionReasonStatistics("Reason", 2, 1)
    except ValueError as exc:
        assert str(exc) == "Exclusion reason count cannot exceed total exclusions"
    else:
        raise AssertionError("Expected ValueError")
