from psi_jarvis.domain.screening.rules.evaluation import evaluate_rule
from psi_jarvis.domain.screening.rules.logical import AllOfRule, AnyOfRule, NotRule
from psi_jarvis.domain.screening.rules.text_rule import TextRule


def test_leaf_rule_creates_trace():
    evaluation = evaluate_rule(TextRule("memory"), "memory study")

    assert evaluation.trace is not None
    assert evaluation.trace.rule_id == "text:memory"
    assert evaluation.trace.kind == "text"
    assert evaluation.trace.matched is True
    assert evaluation.trace.children == ()


def test_nested_rule_creates_recursive_trace():
    rule = AnyOfRule((
        AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
        NotRule(TextRule("animal")),
    ))

    trace = evaluate_rule(rule, "memory hippocampus study").trace

    assert trace is not None
    assert trace.rule_id == rule.id
    assert trace.kind == "or"
    assert trace.matched is True
    assert len(trace.children) == 2
    assert trace.children[0].kind == "and"
    assert trace.children[0].matched is True
    assert trace.children[1].kind == "not"


def test_failed_nested_rule_is_visible_in_trace():
    rule = AllOfRule((TextRule("memory"), TextRule("hippocampus")))

    trace = evaluate_rule(rule, "memory study").trace

    assert trace is not None
    assert trace.matched is False
    assert trace.children[0].matched is True
    assert trace.children[1].matched is False
