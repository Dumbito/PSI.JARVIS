from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_produces_exclusion_reason_analysis():
    criteria = ScreeningCriteria(topic="cognition")
    papers = (
        Paper(title="Cognition study", abstract="cognition"),
        Paper(title="Animal study", abstract="animal"),
        Paper(title="Another animal study", abstract="animal"),
    )

    result = PaperPipeline().process(papers, criteria)
    analysis = result.exclusion_reason_analysis

    assert analysis.total_excluded == 2
    assert analysis.total_reasons == 1
    reason = analysis.by_reason("Topic not found: cognition")
    assert reason is not None
    assert reason.count == 2
    assert reason.rate == 1.0
    assert analysis.total_excluded == result.statistics.excluded_papers
    assert sum(item.rate for item in analysis.reasons) == 1.0
