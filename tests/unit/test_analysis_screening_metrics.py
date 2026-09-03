from psi_jarvis.domain.analysis.screening_metrics import ScreeningMetrics


def test_screening_metrics_rates_and_rule_averages():
    metrics = ScreeningMetrics(
        total_input=10,
        screened_papers=8,
        included_papers=3,
        excluded_papers=5,
        duplicates_removed=2,
        total_matched_rules=12,
        total_failed_rules=4,
    )

    assert metrics.screening_completion_rate == 0.8
    assert metrics.screening_yield == 0.3
    assert metrics.exclusion_yield == 0.5
    assert metrics.average_matched_rules == 1.5
    assert metrics.average_failed_rules == 0.5


def test_screening_metrics_from_audits():
    from uuid import uuid4

    from psi_jarvis.domain.screening.audit import ScreeningAudit

    audits = (
        ScreeningAudit(
            paper_id=uuid4(),
            included=True,
            reason="Included",
            matched_rule_ids=("topic", "population"),
            failed_rule_ids=(),
        ),
        ScreeningAudit(
            paper_id=uuid4(),
            included=False,
            reason="Excluded",
            matched_rule_ids=("topic",),
            failed_rule_ids=("population",),
        ),
    )

    metrics = ScreeningMetrics.from_audits(
        total_input=3,
        screened_papers=2,
        included_papers=1,
        excluded_papers=1,
        duplicates_removed=1,
        audits=audits,
    )

    assert metrics.total_matched_rules == 3
    assert metrics.total_failed_rules == 1
    assert metrics.average_matched_rules == 1.5
    assert metrics.average_failed_rules == 0.5


def test_screening_metrics_zero_division_is_safe():
    metrics = ScreeningMetrics(
        total_input=0,
        screened_papers=0,
        included_papers=0,
        excluded_papers=0,
        duplicates_removed=0,
        total_matched_rules=0,
        total_failed_rules=0,
    )

    assert metrics.screening_completion_rate == 0.0
    assert metrics.screening_yield == 0.0
    assert metrics.exclusion_yield == 0.0
    assert metrics.average_matched_rules == 0.0
    assert metrics.average_failed_rules == 0.0


def test_screening_metrics_rejects_inconsistent_counts():
    try:
        ScreeningMetrics(
            total_input=10,
            screened_papers=7,
            included_papers=3,
            excluded_papers=3,
            duplicates_removed=2,
            total_matched_rules=0,
            total_failed_rules=0,
        )
    except ValueError as exc:
        assert str(exc) == "Included and excluded papers must equal screened papers"
    else:
        raise AssertionError("Expected ValueError")
