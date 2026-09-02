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


import pytest
from uuid import uuid4

from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.domain.screening.execution import ScreeningExecution
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.infrastructure.sqlite_screening_execution_repository import SQLiteScreeningExecutionRepository

def make_execution_with_data() -> ScreeningExecution:
    run = ScreeningRun.create(criteria_version="criteria-v1", total_input=1, unique_papers=1, duplicates_removed=0, screened_papers=1)
    paper_id = uuid4()
    result = ScreeningResult(paper_id=paper_id, included=True, reason="included", run_id=run.run_id, criteria_version="criteria-v1")
    audit = ScreeningAudit.from_result(result)
    return ScreeningExecution(run=run, results=(result,), audits=(audit,))

def test_save_rolls_back_entire_execution_on_failure(tmp_path, monkeypatch):
    import sqlite3
    from psi_jarvis.infrastructure import sqlite_screening_persistence as persistence

    database_path = str(tmp_path / "screening.db")
    repository = SQLiteScreeningExecutionRepository(database_path)
    execution = make_execution_with_data()

    def failing_save_result(connection, result):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(persistence, "save_result", failing_save_result)

    with pytest.raises(RuntimeError, match="forced failure"):
        repository.save(execution)

    with sqlite3.connect(database_path) as connection:
        for table in ("screening_runs", "screening_results", "screening_audits", "screening_executions"):
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count == 0, f"{table} still contains {count} rows"
