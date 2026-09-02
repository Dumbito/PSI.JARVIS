from psi_jarvis.domain.criteria.screening import ScreeningCriteria


def test_criteria_exposes_combined_inclusion_rule():
    criteria = ScreeningCriteria(
        topic="memory",
        inclusion=("hippocampus", "cognition"),
    )

    assert criteria.inclusion_rule.matches("memory hippocampus cognition")
    assert not criteria.inclusion_rule.matches("memory hippocampus")


def test_criteria_exposes_combined_exclusion_rule():
    criteria = ScreeningCriteria(
        topic="memory",
        exclusion=("animal", "pediatric"),
    )

    assert criteria.exclusion_rule.matches("animal memory")
    assert criteria.exclusion_rule.matches("pediatric memory")
    assert not criteria.exclusion_rule.matches("adult human memory")


def test_empty_inclusion_rule_matches():
    criteria = ScreeningCriteria(topic="memory")

    assert criteria.inclusion_rule.matches("anything")


def test_empty_exclusion_rule_does_not_match():
    criteria = ScreeningCriteria(topic="memory")

    assert not criteria.exclusion_rule.matches("anything")
