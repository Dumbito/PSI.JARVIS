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
