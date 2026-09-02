from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.engine import ScreeningEngine
from psi_jarvis.domain.screening.rules.logical import AllOfRule, AnyOfRule, NotRule
from psi_jarvis.domain.screening.rules.text_rule import TextRule


def test_arbitrary_nested_expression_matches():
    expression = AnyOfRule((
        AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
        AllOfRule((TextRule("cognition"), NotRule(TextRule("animal")))),
    ))

    assert expression.matches("memory hippocampus")
    assert expression.matches("human cognition")
    assert not expression.matches("memory only")
    assert not expression.matches("animal cognition")


def test_criteria_accepts_custom_inclusion_expression():
    expression = AnyOfRule((
        AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
        AllOfRule((TextRule("cognition"), NotRule(TextRule("animal")))),
    ))
    criteria = ScreeningCriteria(
        topic="brain",
        inclusion_expression=expression,
    )

    assert criteria.inclusion_rule is expression
    assert criteria.has_custom_logic is True


def test_criteria_accepts_custom_exclusion_expression():
    expression = AnyOfRule((
        TextRule("animal"),
        AllOfRule((TextRule("pediatric"), TextRule("trial"))),
    ))
    criteria = ScreeningCriteria(
        topic="brain",
        exclusion_expression=expression,
    )

    assert criteria.exclusion_rule is expression
    assert criteria.has_custom_logic is True


def test_engine_evaluates_arbitrary_inclusion_tree():
    expression = AnyOfRule((
        AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
        AllOfRule((TextRule("cognition"), NotRule(TextRule("animal")))),
    ))
    criteria = ScreeningCriteria(
        topic="brain",
        inclusion_expression=expression,
    )

    included = ScreeningEngine(criteria).evaluate(
        Paper(title="Brain cognition human study")
    )
    excluded = ScreeningEngine(criteria).evaluate(
        Paper(title="Brain cognition animal study")
    )

    assert included.included is True
    assert excluded.included is False


def test_nested_expression_identity_is_used_for_custom_criteria_version():
    expression = AnyOfRule((
        AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
        NotRule(TextRule("animal")),
    ))
    criteria_a = ScreeningCriteria(topic="brain", inclusion_expression=expression)
    criteria_b = ScreeningCriteria(
        topic="brain",
        inclusion_expression=AnyOfRule((
            AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
            NotRule(TextRule("animal")),
        )),
    )

    assert ScreeningEngine(criteria_a).criteria_version == ScreeningEngine(criteria_b).criteria_version
