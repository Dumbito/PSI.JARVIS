from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.screening_execution_repository import InMemoryScreeningExecutionRepository


def test_pipeline_persists_complete_screening_execution():
    execution_repository = InMemoryScreeningExecutionRepository()
    pipeline = PaperPipeline(execution_repository=execution_repository)
    criteria = ScreeningCriteria(
        topic="intelligence",
        inclusion=("memory",),
        exclusion=("animal",),
    )
    papers = (
        Paper(title="Memory and intelligence", abstract="Study of memory and intelligence."),
    )

    result = pipeline.process(papers, criteria, project_id=None)
    execution = execution_repository.get(result.run.run_id)

    assert execution is not None
    assert execution.run == result.run
    assert execution.results == result.screening_results
    assert execution.audits == result.audits
    assert execution.screened_papers == result.screened_papers
