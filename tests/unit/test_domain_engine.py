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



def test_text_rule_has_stable_identity():
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    rule = TextRule("Intelligence")

    assert rule.id == "text:intelligence"
    assert rule.kind == "text"
    assert rule.value == "Intelligence"


def test_text_rule_identity_is_normalized():
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    first = TextRule("  Intelligence  ")
    second = TextRule("intelligence")

    assert first.id == second.id
    assert first.id == "text:intelligence"



def test_screening_result_can_store_rule_ids():
    from uuid import uuid4
    from psi_jarvis.domain.screening.result import ScreeningResult

    result = ScreeningResult(
        paper_id=uuid4(),
        included=False,
        reason="Exclusion rule matched: animal",
        matched_rule_ids=("text:human",),
        failed_rule_ids=("text:animal",),
    )

    assert result.matched_rule_ids == ("text:human",)
    assert result.failed_rule_ids == ("text:animal",)

def test_screening_result_contains_criteria_version():
    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    criteria = ScreeningCriteria(
        topic="memory",
        inclusion=("adults",),
        exclusion=("animal",),
    )
    engine = ScreeningEngine(criteria)
    paper = Paper(
        title="Memory in adults",
        authors=("Author",),
        abstract="A study about memory in adults.",
    )

    result = engine.evaluate(paper)

    expected = ScreeningCriteriaVersion.from_criteria(criteria).value
    assert result.criteria_version == expected


def test_screening_engine_exposes_criteria_version():
    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    criteria = ScreeningCriteria(topic="memory")
    engine = ScreeningEngine(criteria)

    assert engine.criteria_version == ScreeningCriteriaVersion.from_criteria(criteria).value

def test_screening_run_can_be_created():
    from psi_jarvis.domain.screening.run import ScreeningRun

    run = ScreeningRun.create(
        criteria_version="7c3a0e745f584912",
        total_input=100,
        unique_papers=90,
        duplicates_removed=10,
        screened_papers=90,
    )

    assert run.criteria_version == "7c3a0e745f584912"
    assert run.total_input == 100
    assert run.unique_papers == 90
    assert run.duplicates_removed == 10
    assert run.screened_papers == 90
    assert run.run_id is not None
    assert run.started_at.tzinfo is not None


def test_screening_run_is_immutable():
    from psi_jarvis.domain.screening.run import ScreeningRun

    run = ScreeningRun.create(
        criteria_version="version-a",
        total_input=10,
        unique_papers=10,
        duplicates_removed=0,
        screened_papers=10,
    )

    try:
        run.total_input = 20
    except AttributeError:
        pass
    else:
        raise AssertionError("ScreeningRun should be immutable")


def test_screening_run_rejects_invalid_counts():
    from psi_jarvis.domain.screening.run import ScreeningRun

    try:
        ScreeningRun.create(
            criteria_version="version-a",
            total_input=-1,
            unique_papers=0,
            duplicates_removed=0,
            screened_papers=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("ScreeningRun should reject negative counts")
