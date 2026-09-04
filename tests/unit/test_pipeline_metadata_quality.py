from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_returns_metadata_quality_for_unique_papers():
    papers = (
        Paper(
            title="Memory Study",
            authors=("Author",),
            abstract="Study abstract.",
            doi="10.1234/test",
            publication_year=2026,
            journal="Journal",
        ),
        Paper(
            title="Memory Study",
            authors=("Author",),
            abstract="Study abstract.",
            doi="10.1234/test",
            publication_year=2026,
            journal="Journal",
        ),
        Paper(title="Memory Research"),
    )

    result = PaperPipeline().process(
        papers,
        ScreeningCriteria(topic="memory"),
    )

    assert result.total_input == 3
    assert result.unique_papers == 2
    assert result.metadata_quality.total_papers == 2
    assert result.metadata_quality.by_field("title").present == 2
    assert result.metadata_quality.by_field("authors").present == 1
    assert result.metadata_quality.by_field("abstract").present == 1
    assert result.metadata_quality.by_field("doi").present == 1
    assert result.metadata_quality.by_field("publication_year").present == 1
    assert result.metadata_quality.by_field("journal").present == 1
