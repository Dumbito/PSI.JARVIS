from uuid import uuid4

import pytest

from psi_jarvis.domain.analysis.criteria_analysis import (
    CriteriaAnalysis,
    CriterionStatistics,
)
from psi_jarvis.domain.screening.audit import ScreeningAudit


def test_criterion_statistics_calculates_rates():
    stats = CriterionStatistics(
        criterion_id="text:cognition",
        matched=8,
        failed=2,
    )

    assert stats.evaluated == 10
    assert stats.match_rate == 0.8
    assert stats.failure_rate == 0.2


def test_criterion_statistics_handles_zero_evaluations():
    stats = CriterionStatistics(
        criterion_id="text:cognition",
        matched=0,
        failed=0,
    )

    assert stats.evaluated == 0
    assert stats.match_rate == 0.0
    assert stats.failure_rate == 0.0


def test_criteria_analysis_aggregates_rule_ids_from_audits():
    audits = (
        ScreeningAudit(
            paper_id=uuid4(),
            included=True,
            reason="included",
            matched_rule_ids=("text:cognition", "text:adult"),
        ),
        ScreeningAudit(
            paper_id=uuid4(),
            included=False,
            reason="excluded",
            matched_rule_ids=("text:cognition",),
            failed_rule_ids=("text:adult",),
        ),
    )

    analysis = CriteriaAnalysis.from_audits(audits)

    cognition = analysis.by_criterion_id("text:cognition")
    adult = analysis.by_criterion_id("text:adult")

    assert cognition is not None
    assert cognition.matched == 2
    assert cognition.failed == 0

    assert adult is not None
    assert adult.matched == 1
    assert adult.failed == 1


def test_criteria_analysis_has_deterministic_order():
    audits = (
        ScreeningAudit(
            paper_id=uuid4(),
            included=True,
            reason="included",
            matched_rule_ids=("text:z", "text:a"),
        ),
    )

    analysis = CriteriaAnalysis.from_audits(audits)

    assert tuple(stat.criterion_id for stat in analysis.criteria) == (
        "text:a",
        "text:z",
    )


def test_criteria_analysis_returns_none_for_unknown_criterion():
    analysis = CriteriaAnalysis.from_audits(())

    assert analysis.by_criterion_id("text:unknown") is None


def test_criterion_statistics_rejects_invalid_values():
    with pytest.raises(ValueError):
        CriterionStatistics(
            criterion_id="",
            matched=1,
            failed=0,
        )

    with pytest.raises(ValueError):
        CriterionStatistics(
            criterion_id="text:cognition",
            matched=-1,
            failed=0,
        )