from psi_jarvis.domain.screening import ScreeningDecision


def test_screening_decision_include():
    decision = ScreeningDecision.include(
        reason="Meets all inclusion criteria",
    )

    assert decision.included is True
    assert decision.reason == "Meets all inclusion criteria"


def test_screening_decision_exclude():
    decision = ScreeningDecision.exclude(
        reason="Does not meet the population criterion",
    )

    assert decision.included is False
    assert decision.reason == "Does not meet the population criterion"


def test_screening_decision_is_immutable():
    decision = ScreeningDecision.include(
        reason="Eligible paper",
    )

    try:
        decision.included = False
    except AttributeError:
        pass
    else:
        raise AssertionError("ScreeningDecision should be immutable")

