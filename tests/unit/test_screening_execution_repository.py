from uuid import uuid4

from psi_jarvis.domain.screening.execution import ScreeningExecution
from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.infrastructure.screening_execution_repository import InMemoryScreeningExecutionRepository


def make_execution() -> ScreeningExecution:
    run = ScreeningRun.create(
        criteria_version="criteria-v1",
        total_input=3,
        unique_papers=2,
        duplicates_removed=1,
        screened_papers=2,
    )
    return ScreeningExecution(run=run, results=(), audits=())


def test_save_and_get_execution():
    repository = InMemoryScreeningExecutionRepository()
    execution = make_execution()

    repository.save(execution)

    stored = repository.get(execution.run.run_id)

    assert stored == execution


def test_get_unknown_execution_returns_none():
    repository = InMemoryScreeningExecutionRepository()

    assert repository.get(uuid4()) is None


def test_list_all_returns_saved_executions():
    repository = InMemoryScreeningExecutionRepository()
    first = make_execution()
    second = make_execution()

    repository.save(first)
    repository.save(second)

    stored = repository.list_all()

    assert stored == (first, second)
