from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_produces_decision_distribution():
    criteria = ScreeningCriteria(topic="cognition")
    papers = (
        Paper(title="Cognition study", abstract="cognition"),
        Paper(title="Animal study", abstract="animal"),
    )

    result = PaperPipeline().process(papers, criteria)
    distribution = result.decision_distribution

    assert distribution.total == 2
    assert distribution.included == 1
    assert distribution.excluded == 1
    assert distribution.inclusion_rate == 0.5
    assert distribution.exclusion_rate == 0.5
