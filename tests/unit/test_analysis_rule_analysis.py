from uuid import uuid4

from psi_jarvis.domain.analysis.rule_analysis import RuleAnalysis, RuleStatistics
from psi_jarvis.domain.screening.audit import ScreeningAudit


def make_audit(matched=(), failed=(), included=False):
    return ScreeningAudit(
        paper_id=uuid4(),
        included=included,
        reason="test",
        matched_rule_ids=matched,
        failed_rule_ids=failed,
    )


def test_rule_statistics_rates():
    stats = RuleStatistics(rule_id="inc:cognition", matched=8, failed=2)
    assert stats.evaluated == 10
    assert stats.match_rate == 0.8
    assert stats.failure_rate == 0.2


def test_rule_analysis_counts_rules_from_audits():
    audits = (
        make_audit(matched=("rule:a", "rule:b"), failed=("rule:c",)),
        make_audit(matched=("rule:a",), failed=("rule:c", "rule:d")),
        make_audit(matched=("rule:b",), failed=("rule:d",)),
    )
    analysis = RuleAnalysis.from_audits(audits)
    assert analysis.total_rules == 4
    assert analysis.by_rule_id("rule:a") == RuleStatistics("rule:a", 2, 0)
    assert analysis.by_rule_id("rule:b") == RuleStatistics("rule:b", 2, 0)
    assert analysis.by_rule_id("rule:c") == RuleStatistics("rule:c", 0, 2)
    assert analysis.by_rule_id("rule:d") == RuleStatistics("rule:d", 0, 2)


def test_rule_analysis_empty_audits():
    analysis = RuleAnalysis.from_audits(())
    assert analysis.total_rules == 0
    assert analysis.rules == ()
    assert analysis.by_rule_id("missing") is None


def test_rule_statistics_reject_negative_values():
    try:
        RuleStatistics(rule_id="rule:x", matched=-1, failed=0)
    except ValueError as exc:
        assert str(exc) == "Rule statistics cannot be negative"
    else:
        raise AssertionError("Expected ValueError")
