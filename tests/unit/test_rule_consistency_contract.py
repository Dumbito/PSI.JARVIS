from uuid import uuid4

from psi_jarvis.domain.analysis.rule_consistency import (
    RuleConsistency,
    RuleStatistics,
)
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion
from psi_jarvis.domain.screening.result import ScreeningResult


def test_rule_statistics_rejects_empty_rule_id():
    try:
        RuleStatistics(rule_id="", matched=0, failed=0)
    except ValueError as exc:
        assert str(exc) == "Rule ID cannot be empty"
    else:
        raise AssertionError("Empty rule IDs must be rejected")


def test_rule_consistency_rejects_duplicate_result_papers():
    paper_id = uuid4()
    criteria = ScreeningCriteria(topic="cognition")
    version = ScreeningCriteriaVersion.from_criteria(criteria).value

    result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="test",
        criteria_version=version,
    )

    try:
        RuleConsistency.from_results(
            criteria=criteria,
            results=(result, result),
        )
    except ValueError as exc:
        assert str(exc) == "Results must not contain duplicate papers"
    else:
        raise AssertionError("Duplicate result papers must be rejected")


def test_rule_consistency_requires_matching_criteria_version():
    paper_id = uuid4()
    criteria = ScreeningCriteria(topic="cognition")

    result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="test",
        criteria_version="wrong-version",
    )

    try:
        RuleConsistency.from_results(
            criteria=criteria,
            results=(result,),
        )
    except ValueError as exc:
        assert str(exc) == "Results do not match criteria version"
    else:
        raise AssertionError("Mismatched criteria versions must be rejected")
