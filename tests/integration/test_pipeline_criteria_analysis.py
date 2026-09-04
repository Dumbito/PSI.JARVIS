from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_exposes_criteria_analysis():
    criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=("adult",),
    )

    papers = (
        Paper(
            title="Cognition and adult development",
            abstract="Study about cognition in adult participants.",
        ),
        Paper(
            title="Cognition study",
            abstract="Study about cognition.",
        ),
        Paper(
            title="Animal behavior study",
            abstract="Study about animal behavior.",
        ),
    )

    result = PaperPipeline().process(papers, criteria)

    analysis = result.criteria_analysis

    adult = analysis.by_criterion_id("text:adult")
    cognition = analysis.by_criterion_id("text:cognition")

    assert adult is not None
    assert adult.matched == 1
    assert adult.failed == 1

    assert cognition is not None
    assert cognition.matched == 0
    assert cognition.failed == 1

    assert analysis.total_criteria == 2
