from uuid import uuid4

from psi_jarvis.domain.analysis.rule_consistency import RuleConsistency
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.engine import ScreeningEngine


def make_paper(title: str, abstract: str) -> Paper:
    return Paper(
        id=uuid4(),
        title=title,
        authors=(),
        abstract=abstract,
        doi=None,
        pmid=None,
        publication_year=None,
        journal=None,
    )


def test_rule_consistency_tracks_rule_usage():
    papers = (
        make_paper("Cognition and memory", "cognition memory"),
        make_paper("Cognition only", "cognition"),
        make_paper("Other study", "other"),
    )

    criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=("memory",),
    )

    engine = ScreeningEngine(criteria)
    results = tuple(engine.evaluate(paper) for paper in papers)

    analysis = RuleConsistency.from_results(criteria, results)

    assert analysis.total_results == 3
    assert analysis.included_results == 1
    assert analysis.excluded_results == 2
    assert analysis.consistent is True
    assert analysis.rule_count >= 2
    assert all(rule.evaluated >= 1 for rule in analysis.rules)


def test_rule_consistency_detects_unknown_rule_ids():
    paper = make_paper("Cognition", "cognition")
    criteria = ScreeningCriteria(topic="cognition")
    result = ScreeningEngine(criteria).evaluate(paper)

    from dataclasses import replace
    result = replace(result, matched_rule_ids=("unknown-rule",))

    analysis = RuleConsistency.from_results(
        criteria=criteria,
        results=(result,),
    )

    assert analysis.consistent is False
    assert analysis.untracked_rule_ids == ("unknown-rule",)



def test_rule_consistency_does_not_double_count_rule_trace_and_result_ids():
    from dataclasses import replace
    from psi_jarvis.domain.screening.rules.trace import RuleTrace

    paper = make_paper("Cognition and memory", "cognition memory")
    criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=("memory",),
    )

    result = ScreeningEngine(criteria).evaluate(paper)

    rule_id = result.matched_rule_ids[0]

    result = replace(
        result,
        rule_traces=(
            RuleTrace(
                rule_id=rule_id,
                kind="text",
                matched=True,
            ),
        ),
    )

    analysis = RuleConsistency.from_results(
        criteria=criteria,
        results=(result,),
    )

    rule = next(
        item for item in analysis.rules
        if item.rule_id == rule_id
    )

    assert rule.matched == 1
    assert rule.failed == 0
    assert rule.evaluated == 1




def test_rule_consistency_counts_nested_trace_nodes_once():
    from dataclasses import replace
    from psi_jarvis.domain.screening.rules.trace import RuleTrace

    paper = make_paper("Cognition and memory", "cognition memory")
    criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=("memory",),
    )

    result = ScreeningEngine(criteria).evaluate(paper)

    result = replace(
        result,
        rule_traces=(
            RuleTrace(
                rule_id="custom-parent",
                kind="and",
                matched=True,
                children=(
                    RuleTrace(
                        rule_id="custom-child",
                        kind="text",
                        matched=True,
                    ),
                ),
            ),
        ),
    )

    analysis = RuleConsistency.from_results(
        criteria=criteria,
        results=(result,),
    )

    parent = next(
        item for item in analysis.rules
        if item.rule_id == "custom-parent"
    )
    child = next(
        item for item in analysis.rules
        if item.rule_id == "custom-child"
    )

    assert parent.matched == 1
    assert parent.failed == 0
    assert parent.evaluated == 1

    assert child.matched == 1
    assert child.failed == 0
    assert child.evaluated == 1
