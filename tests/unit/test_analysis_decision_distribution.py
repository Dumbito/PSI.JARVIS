from psi_jarvis.domain.analysis.decision_distribution import DecisionDistribution


def test_decision_distribution_rates():
    distribution = DecisionDistribution(total=10, included=4, excluded=6)
    assert distribution.inclusion_rate == 0.4
    assert distribution.exclusion_rate == 0.6
    assert distribution.counts == {"included": 4, "excluded": 6}


def test_decision_distribution_zero_total():
    distribution = DecisionDistribution(total=0, included=0, excluded=0)
    assert distribution.inclusion_rate == 0.0
    assert distribution.exclusion_rate == 0.0


def test_decision_distribution_rejects_negative_counts():
    try:
        DecisionDistribution(total=1, included=-1, excluded=2)
    except ValueError as exc:
        assert str(exc) == "Decision counts cannot be negative"
    else:
        raise AssertionError("Expected ValueError")


def test_decision_distribution_rejects_invalid_total():
    try:
        DecisionDistribution(total=5, included=2, excluded=2)
    except ValueError as exc:
        assert str(exc) == "Included and excluded decisions must equal total"
    else:
        raise AssertionError("Expected ValueError")
