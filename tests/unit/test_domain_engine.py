from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.screening.engine import ScreeningEngine
from psi_jarvis.domain.screening.result import ScreeningResult


def test_engine_includes_matching_paper():
    paper = Paper(
        title="Working memory and intelligence in adolescents",
        abstract="Study of working memory and intelligence.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
    )

    engine = ScreeningEngine(criteria)
    result = engine.evaluate(paper)

    assert isinstance(result, ScreeningResult)
    assert result.paper_id == paper.id
    assert result.included is True
    assert result.reason == "Paper matches screening criteria"


def test_engine_excludes_non_matching_paper():
    paper = Paper(
        title="Sleep and memory",
        abstract="Study of sleep patterns.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
    )

    engine = ScreeningEngine(criteria)
    result = engine.evaluate(paper)

    assert isinstance(result, ScreeningResult)
    assert result.paper_id == paper.id
    assert result.included is False
    assert "Topic not found" in result.reason


def test_engine_is_case_insensitive():
    paper = Paper(
        title="INTELLIGENCE and cognitive performance",
        abstract="Study of INTELLIGENCE.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
    )

    engine = ScreeningEngine(criteria)
    result = engine.evaluate(paper)

    assert result.included is True
