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



def test_engine_records_matched_exclusion_rules():
    paper = Paper(
        title="Intelligence in adults",
        abstract="Study including animal models and human participants.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
        exclusion=("animal",),
    )

    result = ScreeningEngine(criteria).evaluate(paper)

    assert result.included is False
    assert result.reason == "Exclusion rule matched: animal"
    assert result.failed_rules == ("animal",)


def test_engine_records_all_matched_exclusion_rules():
    paper = Paper(
        title="Intelligence in adults",
        abstract="Study including animal models and clinical participants.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
        exclusion=("animal", "clinical"),
    )

    result = ScreeningEngine(criteria).evaluate(paper)

    assert result.included is False
    assert result.failed_rules == ("animal", "clinical")
    assert result.reason == "Exclusion rule matched: animal"


def test_engine_records_matched_and_failed_inclusion_rules():
    paper = Paper(
        title="Intelligence and memory in adults",
        abstract="Study of intelligence and memory.",
    )

    criteria = ScreeningCriteria(
        topic="intelligence",
        inclusion=("adults", "children"),
    )

    result = ScreeningEngine(criteria).evaluate(paper)

    assert result.included is False
    assert result.reason == "Inclusion rule not matched: children"
    assert result.matched_rules == ("adults",)
    assert result.failed_rules == ("children",)



def test_text_rule_matches_case_insensitively():
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    rule = TextRule("Intelligence")

    assert rule.matches("Study of intelligence and memory") is True
    assert rule.matches("Study of sleep") is False


def test_text_rule_rejects_empty_value():
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    try:
        TextRule("   ")
    except ValueError:
        pass
    else:
        raise AssertionError("TextRule should reject an empty value")
