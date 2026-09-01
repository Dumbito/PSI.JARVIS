from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.screening import ScreeningDecision
from psi_jarvis.domain.screening.engine import ScreeningEngine


def test_engine_includes_matching_paper():
    paper = Paper(
        title="Working memory and intelligence in adolescents",
        abstract="Study of working memory and intelligence.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
    )

    engine = ScreeningEngine(criteria)

    decision = engine.evaluate(paper)

    assert isinstance(decision, ScreeningDecision)
    assert decision.included is True


def test_engine_excludes_non_matching_paper():
    paper = Paper(
        title="Sleep quality in adults",
        abstract="Study of sleep patterns.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
    )

    engine = ScreeningEngine(criteria)

    decision = engine.evaluate(paper)

    assert decision.included is False


def test_engine_is_case_insensitive():
    paper = Paper(
        title="INTELLIGENCE and memory",
        abstract="Cognitive study.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
    )

    engine = ScreeningEngine(criteria)

    decision = engine.evaluate(paper)

    assert decision.included is True
