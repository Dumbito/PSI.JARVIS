from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.criteria.screening import ScreeningCriteria


def test_pipeline_exists():
    assert PaperPipeline() is not None


def test_pipeline_processes_papers():
    papers = [
        Paper(title="Memory and Intelligence", doi="10.1234/a"),
        Paper(title="Unrelated Topic", doi="10.1234/b"),
    ]

    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process(papers, criteria)

    assert result.total_input == 2
    assert result.unique_papers == 2
    assert result.screened_papers == 2


def test_pipeline_normalizes_and_deduplicates():
    papers = [
        Paper(
            title="  Memory   and   Intelligence  ",
            doi="https://doi.org/10.1234/ABC",
        ),
        Paper(
            title="Memory and Intelligence",
            doi="10.1234/abc",
        ),
    ]

    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process(papers, criteria)

    assert result.total_input == 2
    assert result.unique_papers == 1
    assert result.duplicates_removed == 1


def test_pipeline_returns_screening_results():
    papers = [
        Paper(title="Memory and Intelligence", doi="10.1234/a"),
        Paper(title="Unrelated Topic", doi="10.1234/b"),
    ]

    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process(papers, criteria)

    assert len(result.screening_results) == 2
    assert result.screening_results[0].included is True
    assert result.screening_results[1].included is False


def test_pipeline_preserves_processing_order():
    papers = [
        Paper(title="Memory Study", doi="10.1234/a"),
        Paper(title="Brain Study", doi="10.1234/b"),
        Paper(title="Cognition Study", doi="10.1234/c"),
    ]

    criteria = ScreeningCriteria(topic="study")

    result = PaperPipeline().process(papers, criteria)

    assert [paper.title for paper in result.papers] == [
        "Memory Study",
        "Brain Study",
        "Cognition Study",
    ]
