from psi_jarvis.domain.screening.execution import ScreeningExecution
from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.infrastructure.sqlite_screening_execution_repository import SQLiteScreeningExecutionRepository


def make_execution() -> ScreeningExecution:
    run = ScreeningRun.create(
        criteria_version="criteria-v1",
        total_input=3,
        unique_papers=2,
        duplicates_removed=1,
        screened_papers=2,
    )
    return ScreeningExecution(run=run, results=(), audits=())


def test_save_and_get_execution(tmp_path):
    repository = SQLiteScreeningExecutionRepository(str(tmp_path / "screening.db"))
    execution = make_execution()

    repository.save(execution)

    stored = repository.get(execution.run.run_id)

    assert stored == execution


def test_get_unknown_execution_returns_none(tmp_path):
    repository = SQLiteScreeningExecutionRepository(str(tmp_path / "screening.db"))

    from uuid import uuid4

    assert repository.get(uuid4()) is None


def test_list_all_returns_saved_executions(tmp_path):
    repository = SQLiteScreeningExecutionRepository(str(tmp_path / "screening.db"))
    first = make_execution()
    second = make_execution()

    repository.save(first)
    repository.save(second)

    assert repository.list_all() == (first, second)


def test_execution_survives_repository_reinstantiation(tmp_path):
    database_path = str(tmp_path / "screening.db")
    execution = make_execution()

    SQLiteScreeningExecutionRepository(database_path).save(execution)

    reopened = SQLiteScreeningExecutionRepository(database_path)

    assert reopened.get(execution.run.run_id) == execution
