from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_returns_deduplication_analysis():
    papers = (
        Paper(title="Study A", doi="10.1234/test"),
        Paper(title="Study A duplicate", doi="10.1234/test"),
        Paper(title="Study B"),
        Paper(title="Study C"),
    )

    result = PaperPipeline().process(
        papers,
        ScreeningCriteria(topic="study"),
    )

    assert result.total_input == 4
    assert result.unique_papers == 3
    assert result.deduplication_analysis.total_input == 4
    assert result.deduplication_analysis.unique_papers == 3
    assert result.deduplication_analysis.duplicate_papers == 1
    assert result.deduplication_analysis.duplicate_rate == 0.25
