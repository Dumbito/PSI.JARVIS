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
