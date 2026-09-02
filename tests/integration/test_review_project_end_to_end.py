from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.application.project.create_review_project import CreateReviewProjectService
from psi_jarvis.application.project.screen_review_project import ScreenReviewProjectService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository
from psi_jarvis.infrastructure.sqlite_screening_audit_repository import SQLiteScreeningAuditRepository
from psi_jarvis.infrastructure.sqlite_screening_execution_repository import SQLiteScreeningExecutionRepository
from psi_jarvis.infrastructure.sqlite_screening_result_repository import SQLiteScreeningResultRepository
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository


def test_review_project_end_to_end_with_sqlite_persistence(tmp_path):
    database_path = tmp_path / "psi_jarvis.db"

    project_repository = SQLiteProjectRepository(database_path)
    run_repository = SQLiteScreeningRunRepository(database_path)
    result_repository = SQLiteScreeningResultRepository(database_path)
    audit_repository = SQLiteScreeningAuditRepository(database_path)
    execution_repository = SQLiteScreeningExecutionRepository(database_path)

    pipeline = PaperPipeline(
        run_repository=run_repository,
        result_repository=result_repository,
        audit_repository=audit_repository,
        execution_repository=execution_repository,
    )

    create_project = CreateReviewProjectService(project_repository)
    screen_project = ScreenReviewProjectService(project_repository, pipeline)

    criteria = ScreeningCriteria(
        topic="memory",
        inclusion=("cognition",),
        exclusion=("animal",),
    )

    project = create_project.execute(
        name="Memory and Cognition Review",
        research_question="How is memory related to cognition?",
        criteria=criteria,
    )

    papers = [
        Paper(
            title="Memory and Cognition",
            abstract="Human memory and cognition are closely related.",
            doi="10.1000/test-memory-1",
        ),
        Paper(
            title="Memory and Cognition",
            abstract="Human memory and cognition are closely related.",
            doi="10.1000/test-memory-1",
        ),
        Paper(
            title="Memory in Animal Models",
            abstract="Animal models are used to study memory.",
            doi="10.1000/test-memory-2",
        ),
    ]

    result = screen_project.execute(project.project_id, papers)

    assert result.total_input == 3
    assert result.unique_papers == 2
    assert result.duplicates_removed == 1
    assert result.screened_papers == 2
    assert len(result.screening_results) == 2
    assert len(result.audits) == 2
    assert result.run.project_id == project.project_id

    included = [item for item in result.screening_results if item.included]
    excluded = [item for item in result.screening_results if not item.included]

    assert len(included) == 1
    assert len(excluded) == 1
    assert excluded[0].reason

    run_id = result.run.run_id

    assert run_repository.get(run_id) is not None
    assert len(result_repository.list_all()) == 2
    assert len(audit_repository.list_all()) == 2

    execution = execution_repository.get(run_id)
    assert execution is not None
    assert execution.run.run_id == run_id
    assert len(execution.results) == 2
    assert len(execution.audits) == 2

    reloaded_project_repository = SQLiteProjectRepository(database_path)
    reloaded_run_repository = SQLiteScreeningRunRepository(database_path)
    reloaded_result_repository = SQLiteScreeningResultRepository(database_path)
    reloaded_audit_repository = SQLiteScreeningAuditRepository(database_path)
    reloaded_execution_repository = SQLiteScreeningExecutionRepository(database_path)

    reloaded_project = reloaded_project_repository.get(project.project_id)
    reloaded_run = reloaded_run_repository.get(run_id)
    reloaded_execution = reloaded_execution_repository.get(run_id)

    assert reloaded_project is not None
    assert reloaded_project.project_id == project.project_id
    assert reloaded_project.criteria == project.criteria

    assert reloaded_run is not None
    assert reloaded_run.project_id == project.project_id

    assert reloaded_execution is not None
    assert reloaded_execution.run.run_id == run_id
    assert len(reloaded_execution.results) == 2
    assert len(reloaded_execution.audits) == 2
    assert len(reloaded_result_repository.list_all()) == 2
    assert len(reloaded_audit_repository.list_all()) == 2
