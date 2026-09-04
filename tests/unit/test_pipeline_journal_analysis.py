from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_returns_journal_analysis_for_unique_papers():
    papers = (
        Paper(title="Study A", journal="Journal A", doi="10.1234/test"),
        Paper(title="Study A", journal="Journal A", doi="10.1234/test"),
        Paper(title="Study B", journal="Journal B"),
        Paper(title="Study C"),
    )

    result = PaperPipeline().process(
        papers,
        ScreeningCriteria(topic="study"),
    )

    assert result.total_input == 4
    assert result.unique_papers == 3
    assert result.journal_analysis.total_papers == 3
    assert result.journal_analysis.papers_with_journal == 2
    assert result.journal_analysis.papers_without_journal == 1
    assert result.journal_analysis.unique_journals == 2
    assert result.journal_analysis.by_journal == (("Journal A", 1), ("Journal B", 1))
    assert result.journal_analysis.journal_coverage_rate == 2 / 3
