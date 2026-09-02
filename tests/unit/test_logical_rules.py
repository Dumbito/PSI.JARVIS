from psi_jarvis.domain.screening.rules.logical import AllOfRule, AnyOfRule, NotRule
from psi_jarvis.domain.screening.rules.text_rule import TextRule


def test_all_of_rule_requires_every_rule():
    rule = AllOfRule((TextRule("memory"), TextRule("hippocampus")))

    assert rule.matches("memory and hippocampus")
    assert not rule.matches("memory without the second term")


def test_any_of_rule_requires_one_matching_rule():
    rule = AnyOfRule((TextRule("memory"), TextRule("cognition")))

    assert rule.matches("cognition study")
    assert rule.matches("memory study")
    assert not rule.matches("motor study")


def test_not_rule_inverts_match():
    rule = NotRule(TextRule("animal"))

    assert rule.matches("human study")
    assert not rule.matches("animal study")


def test_logical_rule_ids_are_stable():
    first = AllOfRule((TextRule("Memory"), TextRule("Hippocampus")))
    second = AllOfRule((TextRule("memory"), TextRule("hippocampus")))

    assert first.id == second.id
    assert first.id == "and:(text:memory,text:hippocampus)"


def test_nested_logical_rule_id_is_stable():
    rule = AnyOfRule(
        (
            AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
            NotRule(TextRule("animal")),
        )
    )

    assert rule.id == "or:(and:(text:memory,text:hippocampus),not:(text:animal))"


def test_empty_all_of_rule_matches_empty_set():
    assert AllOfRule(()).matches("anything")


def test_empty_any_of_rule_does_not_match():
    assert not AnyOfRule(()).matches("anything")
