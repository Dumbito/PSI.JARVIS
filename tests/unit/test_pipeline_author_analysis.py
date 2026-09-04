from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_returns_author_analysis_for_unique_papers():
    papers = (
        Paper(title="Study A", authors=("Alice", "Bob"), doi="10.1234/test"),
        Paper(title="Study A", authors=("Alice", "Bob"), doi="10.1234/test"),
        Paper(title="Study B", authors=("Carol",)),
        Paper(title="Study C"),
    )

    result = PaperPipeline().process(
        papers,
        ScreeningCriteria(topic="study"),
    )

    assert result.total_input == 4
    assert result.unique_papers == 3
    assert result.author_analysis.total_papers == 3
    assert result.author_analysis.papers_with_authors == 2
    assert result.author_analysis.papers_without_authors == 1
    assert result.author_analysis.unique_authors == 3
    assert result.author_analysis.by_author == (("Alice", 1), ("Bob", 1), ("Carol", 1))
    assert result.author_analysis.author_coverage_rate == 2 / 3
