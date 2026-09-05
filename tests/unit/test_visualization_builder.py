from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.visualization import SVGChartRenderer, VisualizationBuilder
from psi_jarvis.domain.criteria import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_visualization_builder_uses_pipeline_analyses():
    pipeline = PaperPipeline()
    criteria = ScreeningCriteria(topic="intelligence")
    papers = (
        Paper(
            title="Intelligence study",
            abstract="Intelligence research.",
            publication_year=2025,
        ),
        Paper(
            title="Animal study",
            abstract="Animal research.",
            publication_year=2024,
        ),
    )

    result = pipeline.process(papers, criteria)
    bundle = VisualizationBuilder(SVGChartRenderer()).execute(result)

    assert "<svg" in bundle.decision_distribution
    assert "<svg" in bundle.publication_year
    assert "<svg" in bundle.exclusion_reasons


def test_visualization_builder_is_deterministic():
    pipeline = PaperPipeline()
    criteria = ScreeningCriteria(topic="intelligence")
    papers = (
        Paper(
            title="Intelligence study",
            abstract="Intelligence research.",
            publication_year=2025,
        ),
    )

    result = pipeline.process(papers, criteria)
    builder = VisualizationBuilder(SVGChartRenderer())

    first = builder.execute(result)
    second = builder.execute(result)

    assert first == second


def test_visualization_builder_accepts_custom_renderer_dimensions():
    pipeline = PaperPipeline()
    criteria = ScreeningCriteria(topic="intelligence")
    result = pipeline.process(
        (Paper(title="Intelligence", abstract="Intelligence research."),),
        criteria,
    )

    builder = VisualizationBuilder(SVGChartRenderer(width=600, height=400))
    bundle = builder.execute(result)

    assert "width=" + chr(34) + "600" + chr(34) in bundle.decision_distribution
    assert "height=" + chr(34) + "400" + chr(34) in bundle.decision_distribution
