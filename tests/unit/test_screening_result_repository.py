from uuid import uuid4

from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.infrastructure.screening_result_repository import (
    InMemoryScreeningResultRepository,
)


def make_result(run_id=None):
    return ScreeningResult(
        paper_id=uuid4(),
        included=True,
        reason="Paper matches screening criteria",
        run_id=run_id,
    )


def test_save_and_get_result():
    repository = InMemoryScreeningResultRepository()
    run_id = uuid4()
    result = make_result(run_id)

    repository.save(result)

    assert repository.get(result.paper_id, run_id) == result


def test_get_unknown_result_returns_none():
    repository = InMemoryScreeningResultRepository()

    assert repository.get(uuid4()) is None


def test_list_all_returns_saved_results():
    repository = InMemoryScreeningResultRepository()
    first = make_result(uuid4())
    second = make_result(uuid4())

    repository.save(first)
    repository.save(second)

    assert repository.list_all() == (first, second)


def test_save_replaces_same_result_identity():
    repository = InMemoryScreeningResultRepository()
    run_id = uuid4()
    first = make_result(run_id)
    replacement = ScreeningResult(
        paper_id=first.paper_id,
        included=False,
        reason="Replacement",
        run_id=run_id,
    )

    repository.save(first)
    repository.save(replacement)

    assert repository.get(first.paper_id, run_id) == replacement
    assert len(repository.list_all()) == 1


def test_same_paper_can_have_results_in_different_runs():
    repository = InMemoryScreeningResultRepository()
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
