from psi_jarvis.domain.criteria.screening import ScreeningCriteria


def test_screening_criteria_minimal():
    criteria = ScreeningCriteria(
        topic="working memory",
    )

    assert criteria.topic == "working memory"
    assert criteria.inclusion == ()
    assert criteria.exclusion == ()


def test_screening_criteria_with_rules():
    criteria = ScreeningCriteria(
        topic="working memory",
        inclusion=(
            "Human participants",
            "Adults",
            "Experimental study",
        ),
        exclusion=(
            "Animal studies",
            "Case reports",
        ),
    )

    assert criteria.topic == "working memory"
    assert criteria.inclusion == (
        "Human participants",
        "Adults",
        "Experimental study",
    )
    assert criteria.exclusion == (
        "Animal studies",
        "Case reports",
    )


def test_screening_criteria_is_immutable():
    criteria = ScreeningCriteria(
        topic="working memory",
    )

    try:
        criteria.topic = "memory"
    except AttributeError:
        pass
    else:
        raise AssertionError("ScreeningCriteria should be immutable")



def test_screening_criteria_rejects_empty_topic():
    try:
        ScreeningCriteria(topic="")
    except ValueError:
        pass
    else:
        raise AssertionError("ScreeningCriteria should reject an empty topic")


def test_screening_criteria_rejects_whitespace_topic():
    try:
        ScreeningCriteria(topic="   ")
    except ValueError:
        pass
    else:
        raise AssertionError("ScreeningCriteria should reject a whitespace-only topic")


def test_screening_criteria_rejects_empty_inclusion_rule():
    try:
        ScreeningCriteria(
            topic="memory",
            inclusion=("adults", "", "human"),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("ScreeningCriteria should reject empty inclusion rules")


def test_screening_criteria_rejects_empty_exclusion_rule():
    try:
        ScreeningCriteria(
            topic="memory",
            exclusion=("animal", "   "),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("ScreeningCriteria should reject empty exclusion rules")



def test_screening_criteria_exposes_topic_rule():
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    criteria = ScreeningCriteria(topic="working memory")

    assert isinstance(criteria.topic_rule, TextRule)
    assert criteria.topic_rule.value == "working memory"
    assert criteria.topic_rule.id == "text:working memory"


def test_screening_criteria_exposes_inclusion_rules():
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    criteria = ScreeningCriteria(
        topic="memory",
        inclusion=("Adults", "Human participants"),
    )

    assert criteria.inclusion_rules == (
        TextRule("Adults"),
        TextRule("Human participants"),
    )


def test_screening_criteria_exposes_exclusion_rules():
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    criteria = ScreeningCriteria(
        topic="memory",
        exclusion=("Animal studies", "Case reports"),
    )

    assert criteria.exclusion_rules == (
        TextRule("Animal studies"),
        TextRule("Case reports"),
    )

def test_screening_criteria_version_is_stable():
    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    criteria = ScreeningCriteria(
        topic="memory",
        inclusion=("adults", "human"),
        exclusion=("animal",),
    )

    version_a = ScreeningCriteriaVersion.from_criteria(criteria)
    version_b = ScreeningCriteriaVersion.from_criteria(criteria)

    assert version_a == version_b
    assert len(version_a.value) == 16


def test_screening_criteria_version_changes_when_criteria_change():
    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    criteria_a = ScreeningCriteria(
        topic="memory",
        inclusion=("adults",),
    )
    criteria_b = ScreeningCriteria(
        topic="memory",
        inclusion=("children",),
    )

    assert ScreeningCriteriaVersion.from_criteria(criteria_a) != ScreeningCriteriaVersion.from_criteria(criteria_b)


def test_screening_criteria_version_is_immutable():
    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    version = ScreeningCriteriaVersion("abc123")

    try:
        version.value = "changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("ScreeningCriteriaVersion should be immutable")
