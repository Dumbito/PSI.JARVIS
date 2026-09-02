from uuid import uuid4

from psi_jarvis.application.screening.execution import ScreeningExecution, ScreeningExecutionLoader
from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.infrastructure.screening_audit_repository import InMemoryScreeningAuditRepository
from psi_jarvis.infrastructure.screening_result_repository import InMemoryScreeningResultRepository
from psi_jarvis.infrastructure.screening_run_repository import InMemoryScreeningRunRepository


def make_run():
    return ScreeningRun.create(
        criteria_version="version-a",
        total_input=2,
        unique_papers=2,
        duplicates_removed=0,
        screened_papers=2,
    )


def test_execution_rejects_result_from_another_run():
    run = make_run()
    other_run = uuid4()

    result = ScreeningResult(
        paper_id=uuid4(),
        included=True,
        reason="Included",
        run_id=other_run,
    )

    try:
        ScreeningExecution(run=run, results=(result,), audits=())
    except ValueError as error:
        assert "results" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_execution_rejects_audit_from_another_run():
    run = make_run()
    other_run = uuid4()

    audit = ScreeningAudit(
        paper_id=uuid4(),
        included=True,
        reason="Included",
        run_id=other_run,
    )

    try:
        ScreeningExecution(run=run, results=(), audits=(audit,))
    except ValueError as error:
        assert "audits" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_loader_reconstructs_execution():
    run_repository = InMemoryScreeningRunRepository()
    result_repository = InMemoryScreeningResultRepository()
    audit_repository = InMemoryScreeningAuditRepository()

    run = make_run()
    paper_id = uuid4()

    result = ScreeningResult(
        paper_id=paper_id,
        included=True,
        reason="Included",
        run_id=run.run_id,
    )

    audit = ScreeningAudit(
        paper_id=paper_id,
        included=True,
        reason="Included",
        run_id=run.run_id,
    )

    run_repository.save(run)
    result_repository.save(result)
    audit_repository.save(audit)

    execution = ScreeningExecutionLoader(
        run_repository,
        result_repository,
        audit_repository,
    ).load(run.run_id)

    assert execution is not None
    assert execution.run == run
    assert execution.results == (result,)
    assert execution.audits == (audit,)
    assert execution.included == 1
    assert execution.excluded == 0
    assert execution.screened_papers == 1


def test_loader_returns_none_for_unknown_run():
    loader = ScreeningExecutionLoader(
        InMemoryScreeningRunRepository(),
        InMemoryScreeningResultRepository(),
        InMemoryScreeningAuditRepository(),
    )

    assert loader.load(uuid4()) is None


def test_loader_ignores_data_from_other_runs():
    run_repository = InMemoryScreeningRunRepository()
    result_repository = InMemoryScreeningResultRepository()
    audit_repository = InMemoryScreeningAuditRepository()

    run = make_run()
    other_run = make_run()

    current_result = ScreeningResult(
        paper_id=uuid4(),
        included=True,
        reason="Included",
        run_id=run.run_id,
    )
    other_result = ScreeningResult(
        paper_id=uuid4(),
        included=False,
        reason="Excluded",
        run_id=other_run.run_id,
    )

    run_repository.save(run)
    run_repository.save(other_run)
    result_repository.save(current_result)
    result_repository.save(other_result)

    execution = ScreeningExecutionLoader(
        run_repository,
        result_repository,
        InMemoryScreeningAuditRepository(),
    ).load(run.run_id)

    assert execution is not None
    assert execution.results == (current_result,)

def test_loader_reconstructs_execution_from_sqlite(tmp_path):
    from psi_jarvis.domain.criteria.screening import ScreeningCriteria
    from psi_jarvis.domain.paper import Paper
    from psi_jarvis.application.pipeline.pipeline import PaperPipeline
    from psi_jarvis.infrastructure.sqlite_screening_audit_repository import SQLiteScreeningAuditRepository
    from psi_jarvis.infrastructure.sqlite_screening_result_repository import SQLiteScreeningResultRepository
    from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository

    database_path = str(tmp_path / "screening.db")

    run_repository = SQLiteScreeningRunRepository(database_path)
    result_repository = SQLiteScreeningResultRepository(database_path)
    audit_repository = SQLiteScreeningAuditRepository(database_path)

    criteria = ScreeningCriteria(topic="memory")
    papers = [
        Paper(title="Memory Study", doi="10.1234/a"),
        Paper(title="Unrelated Study", doi="10.1234/b"),
    ]

    pipeline_result = PaperPipeline(
        run_repository=run_repository,
        result_repository=result_repository,
        audit_repository=audit_repository,
    ).process(papers, criteria)

    reopened_run_repository = SQLiteScreeningRunRepository(database_path)
    reopened_result_repository = SQLiteScreeningResultRepository(database_path)
    reopened_audit_repository = SQLiteScreeningAuditRepository(database_path)

    execution = ScreeningExecutionLoader(
        reopened_run_repository,
        reopened_result_repository,
        reopened_audit_repository,
    ).load(pipeline_result.run.run_id)

    assert execution is not None
    assert execution.run == pipeline_result.run
    assert execution.results == pipeline_result.screening_results
    assert execution.audits == pipeline_result.audits
    assert execution.screened_papers == 2
    assert execution.included == 1
    assert execution.excluded == 1
