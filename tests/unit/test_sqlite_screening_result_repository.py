from uuid import uuid4

from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.infrastructure.sqlite_screening_result_repository import (
    SQLiteScreeningResultRepository,
)


def make_result(run_id=None):
    return ScreeningResult(
        paper_id=uuid4(),
        included=False,
        reason="Inclusion rule not matched: randomized",
        run_id=run_id,
        matched_rules=("adult",),
        failed_rules=("randomized",),
        matched_rule_ids=("text:adult",),
        failed_rule_ids=("text:randomized",),
        criteria_version="abc123",
    )


def test_save_and_get_result(tmp_path):
    repository = SQLiteScreeningResultRepository(str(tmp_path / "screening.db"))
    run_id = uuid4()
    result = make_result(run_id)

    repository.save(result)

    assert repository.get(result.paper_id, run_id) == result


def test_get_unknown_result_returns_none(tmp_path):
    repository = SQLiteScreeningResultRepository(str(tmp_path / "screening.db"))

    assert repository.get(uuid4()) is None


def test_list_all_returns_saved_results(tmp_path):
    repository = SQLiteScreeningResultRepository(str(tmp_path / "screening.db"))
    first = make_result(uuid4())
    second = make_result(uuid4())

    repository.save(first)
    repository.save(second)

    assert repository.list_all() == (first, second)


def test_save_replaces_same_result_identity(tmp_path):
    repository = SQLiteScreeningResultRepository(str(tmp_path / "screening.db"))
    run_id = uuid4()
    first = make_result(run_id)
    replacement = ScreeningResult(
        paper_id=first.paper_id,
        included=True,
        reason="Paper matches screening criteria",
        run_id=run_id,
        criteria_version="abc123",
    )

    repository.save(first)
    repository.save(replacement)

    assert repository.get(first.paper_id, run_id) == replacement
    assert len(repository.list_all()) == 1


def test_same_paper_can_have_results_in_different_runs(tmp_path):
    repository = SQLiteScreeningResultRepository(str(tmp_path / "screening.db"))
    paper_id = uuid4()
    first_run = uuid4()
    second_run = uuid4()

    first = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="Included",
        run_id=first_run,
    )
    second = ScreeningResult(
        paper_id=paper_id,
        included=False,
        reason="Excluded",
        run_id=second_run,
    )

    repository.save(first)
    repository.save(second)

    assert repository.get(paper_id, first_run) == first
    assert repository.get(paper_id, second_run) == second
    assert len(repository.list_all()) == 2


def test_result_without_run_id_is_persisted(tmp_path):
    repository = SQLiteScreeningResultRepository(str(tmp_path / "screening.db"))
    result = make_result()

    repository.save(result)

    assert repository.get(result.paper_id) == result

def test_rule_trace_survives_sqlite_round_trip(tmp_path):
    from psi_jarvis.domain.screening.rules.logical import AllOfRule, AnyOfRule, NotRule
    from psi_jarvis.domain.screening.rules.evaluation import evaluate_rule
    from psi_jarvis.domain.screening.rules.text_rule import TextRule

    database_path = tmp_path / "screening.db"
    repository = SQLiteScreeningResultRepository(str(database_path))

    rule = AnyOfRule((
        AllOfRule((TextRule("memory"), TextRule("hippocampus"))),
        NotRule(TextRule("animal")),
    ))
    evaluation = evaluate_rule(rule, "memory hippocampus study")

    result = ScreeningResult(
        paper_id=uuid4(),
        included=True,
        reason="Included",
        run_id=uuid4(),
        rule_traces=(evaluation.trace,) if evaluation.trace is not None else (),
    )

    repository.save(result)
    stored = repository.get(result.paper_id, result.run_id)

    assert stored is not None
    assert stored.rule_traces == result.rule_traces
    assert stored.rule_traces[0].children[0].children[0].rule_id == "text:memory"
    assert stored.rule_traces[0].children[0].children[1].rule_id == "text:hippocampus"
    assert stored.rule_traces[0].children[1].children[0].rule_id == "text:animal"
