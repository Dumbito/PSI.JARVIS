from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_returns_publication_year_analysis_for_unique_papers():
    papers = (
        Paper(title="Study 2024", publication_year=2024, doi="10.1234/test"),
        Paper(title="Study 2024", publication_year=2024, doi="10.1234/test"),
        Paper(title="Study 2025", publication_year=2025),
        Paper(title="Study Unknown"),
    )

    result = PaperPipeline().process(
        papers,
        ScreeningCriteria(topic="study"),
    )

    assert result.total_input == 4
    assert result.unique_papers == 3
    assert result.publication_year_analysis.total_papers == 3
    assert result.publication_year_analysis.papers_with_year == 2
    assert result.publication_year_analysis.papers_without_year == 1
    assert result.publication_year_analysis.year_min == 2024
    assert result.publication_year_analysis.year_max == 2025
    assert result.publication_year_analysis.by_year == ((2024, 1), (2025, 1))
    assert result.publication_year_analysis.year_coverage_rate == 2 / 3
